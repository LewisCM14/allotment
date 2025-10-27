import { API_URL, API_VERSION } from "@/services/apiConfig";
import { errorMonitor } from "@/services/errorMonitoring";
import type { ITokenPair } from "@/store/auth/AuthContext";
import axios, {
	type AxiosError,
	type AxiosRequestConfig,
	type AxiosResponse,
} from "axios";

export interface IApiError {
	detail: string | Array<{ msg: string; loc: string[] }>;
	status_code?: number;
}

declare module "axios" {
	interface AxiosRequestConfig {
		_retry?: boolean;
		_retryCount?: number;
	}
}

const extractDetailMessage = (detail: unknown): string | null => {
	if (typeof detail === "string") {
		return detail;
	}

	if (Array.isArray(detail)) {
		const messages = detail
			.map((item) => {
				if (typeof item === "string") {
					return item;
				}
				if (item && typeof item === "object") {
					const itemDetail = item as {
						msg?: unknown;
						message?: unknown;
					};
					let possible: string | null = null;
					if (typeof itemDetail.msg === "string") {
						possible = itemDetail.msg;
					} else if (typeof itemDetail.message === "string") {
						possible = itemDetail.message;
					}
					if (possible) {
						return possible;
					}
				}
				return null;
			})
			.filter((msg): msg is string => Boolean(msg));

		if (messages.length > 0) {
			return messages.join("\n");
		}
	}

	if (detail && typeof detail === "object") {
		const objectDetail = detail as {
			msg?: unknown;
			message?: unknown;
			detail?: unknown;
		};
		let possible: string | null = null;
		if (typeof objectDetail.msg === "string") {
			possible = objectDetail.msg;
		} else if (typeof objectDetail.message === "string") {
			possible = objectDetail.message;
		} else if (typeof objectDetail.detail === "string") {
			possible = objectDetail.detail;
		}
		if (possible) {
			return possible;
		}
	}

	return null;
};

// Custom error that preserves HTTP status codes for UI branching
export class AppError extends Error {
	statusCode?: number;
	detail?: unknown;

	constructor(
		message: string,
		options?: { statusCode?: number; detail?: unknown },
	) {
		super(message);
		this.name = "AppError";
		this.statusCode = options?.statusCode;
		this.detail = options?.detail;
	}
}

export const handleApiError = (
	error: unknown,
	defaultMessage: string,
): never => {
	if (axios.isAxiosError(error)) {
		if (!error.response) {
			throw new AppError(
				"Network error. Please check your connection and try again.",
				{ statusCode: 0 },
			);
		}

		if (error.response.status === 401) {
			throw new AppError("Invalid email or password. Please try again.", {
				statusCode: 401,
				detail: error.response.data,
			});
		}

		if (error.response.status === 500) {
			throw new AppError("Server error. Please try again later.", {
				statusCode: 500,
				detail: error.response.data,
			});
		}

		const errorDetail = error.response?.data?.detail;
		if (errorDetail) {
			const friendlyMessage = extractDetailMessage(errorDetail);
			if (friendlyMessage) {
				throw new AppError(friendlyMessage, {
					statusCode: error.response.status,
					detail: errorDetail,
				});
			}
			if (typeof errorDetail === "string") {
				throw new AppError(errorDetail, {
					statusCode: error.response.status,
					detail: errorDetail,
				});
			}
			throw new AppError(JSON.stringify(errorDetail), {
				statusCode: error.response.status,
				detail: errorDetail,
			});
		}
	}

	// Log to error monitoring
	errorMonitor.captureException(error, { defaultMessage });

	// Fallback to AppError to keep type consistency
	throw new AppError(defaultMessage);
};

// Track in-flight requests for cancellation
const pendingRequests = new Map<string, AbortController>();

// Create the base axios instance
const api = axios.create({
	headers: {
		"Content-Type": "application/json",
		Accept: "application/json",
		"X-Requested-With": "XMLHttpRequest", // Helps prevent CSRF
	},
	withCredentials: true,
});

const checkOnlineStatus = (): boolean => {
	return navigator.onLine;
};

const handleOnlineStatus = () => {
	if (!checkOnlineStatus()) {
		throw new Error("You are offline. Please check your connection.");
	}
};

const handleRequestCancellation = (config: AxiosRequestConfig) => {
	if (!config.url) return;

	// Only cancel requests for certain endpoints that support cancellation
	const cancelableEndpoints = [
		"/search", // Search queries can be safely canceled
		"/autocomplete", // Autocomplete can be safely canceled
		// Add other endpoints that benefit from cancellation
	];

	const shouldCancelDuplicates = cancelableEndpoints.some((endpoint) =>
		config.url?.includes(endpoint),
	);

	if (!shouldCancelDuplicates) {
		return; // Don't cancel for most endpoints
	}

	const requestKey = config.url + JSON.stringify(config.params ?? {});

	if (pendingRequests.has(requestKey)) {
		pendingRequests.get(requestKey)?.abort();
	}

	const controller = new AbortController();
	config.signal = controller.signal;
	pendingRequests.set(requestKey, controller);
};

const addAuthToken = (config: AxiosRequestConfig) => {
	const token = localStorage.getItem("access_token");
	if (token) {
		config.headers ??= {};
		config.headers.Authorization = `Bearer ${token}`;
	}
};

const normalizeUrl = (config: AxiosRequestConfig) => {
	if (!config.url || config.url.startsWith("http")) {
		return;
	}

	if (!config.url.startsWith(API_VERSION)) {
		const apiVersionClean = API_VERSION.endsWith("/")
			? API_VERSION.slice(0, -1)
			: API_VERSION;
		const pathClean = config.url.startsWith("/")
			? config.url
			: `/${config.url}`;
		config.url = apiVersionClean + pathClean;
	}

	if (API_URL && !config.url.startsWith("http")) {
		const apiUrlClean = API_URL.endsWith("/") ? API_URL.slice(0, -1) : API_URL;
		config.url = apiUrlClean + config.url;
	}
};

// Request interceptor
api.interceptors.request.use(
	(config) => {
		handleOnlineStatus();
		handleRequestCancellation(config);
		addAuthToken(config);
		normalizeUrl(config);
		return config;
	},
	(error) => {
		if (error instanceof Error) {
			errorMonitor.captureException(error, { context: "request_interceptor" });
			return Promise.reject(error);
		}
		const err = new Error(String(error));
		errorMonitor.captureException(err, { context: "request_interceptor" });
		return Promise.reject(err);
	},
);

let isRefreshing = false;
let failedQueue: {
	resolve: (value: unknown) => void;
	reject: (reason?: unknown) => void;
	config: AxiosRequestConfig;
}[] = [];

const processQueue = (error: AxiosError | null, token: string | null) => {
	for (const item of failedQueue) {
		if (error) {
			item.reject(error);
		} else if (token) {
			const config = { ...item.config };
			config.headers = { ...config.headers, Authorization: `Bearer ${token}` };
			axios(config).then(
				(response) => item.resolve(response),
				(error) => item.reject(error),
			);
		}
	}

	failedQueue = [];
};

export interface IRefreshRequest {
	refresh_token: string;
}

const refreshAccessToken = async (): Promise<string | null> => {
	const refreshToken = localStorage.getItem("refresh_token");
	if (!refreshToken) return null;

	try {
		const refreshUrl = `${API_URL}${API_VERSION}/auth/token/refresh`;
		const response = await axios.post<ITokenPair>(refreshUrl, {
			refresh_token: refreshToken,
		});

		localStorage.setItem("access_token", response.data.access_token);
		localStorage.setItem("refresh_token", response.data.refresh_token);

		return response.data.access_token;
	} catch (error) {
		// Clear tokens on refresh failure and log the error
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");

		errorMonitor.captureException(error, { context: "token_refresh_failed" });

		return null;
	}
};

const shouldRetryRequest = (error: AxiosError): boolean => {
	if (!error.config) return false;
	const { code, response } = error;
	return (
		code === "ECONNABORTED" ||
		code === "ERR_NETWORK" ||
		(!!response && response.status >= 500 && response.status < 600)
	);
};

const handleRequestRetry = async (error: AxiosError) => {
	if (!error.config) {
		return Promise.reject(error);
	}
	const originalRequest = error.config;
	originalRequest._retryCount = (originalRequest._retryCount ?? 0) + 1;

	if (originalRequest._retryCount > MAX_RETRIES) {
		return Promise.reject(error);
	}

	const delay = RETRY_DELAY_MS * 2 ** (originalRequest._retryCount - 1);

	errorMonitor.captureMessage(
		`Retrying request (${originalRequest._retryCount}/${MAX_RETRIES})`,
		{
			url: originalRequest.url,
			method: originalRequest.method,
			status: error.response?.status,
		},
	);

	await new Promise((resolve) => setTimeout(resolve, delay));
	return api(originalRequest);
};

const handleTokenRefresh = async (error: AxiosError) => {
	if (!error.config) {
		return Promise.reject(
			error instanceof Error ? error : new Error(String(error)),
		);
	}
	const originalRequest = error.config;
	if (isRefreshing) {
		return new Promise((resolve, reject) => {
			failedQueue.push({ resolve, reject, config: originalRequest });
		});
	}

	originalRequest._retry = true;
	isRefreshing = true;

	try {
		const newToken = await refreshAccessToken();
		isRefreshing = false;

		if (newToken) {
			processQueue(null, newToken);
			originalRequest.headers.Authorization = `Bearer ${newToken}`;
			return api(originalRequest);
		}
		processQueue(error, null);
		return Promise.reject(
			error instanceof Error ? error : new Error(String(error)),
		);
	} catch (refreshError) {
		isRefreshing = false;
		processQueue(error, null);

		errorMonitor.captureException(refreshError, {
			context: "token_refresh_failed",
			originalUrl: originalRequest.url,
		});

		window.location.href = "/login";
		return Promise.reject(
			refreshError instanceof Error
				? refreshError
				: new Error(String(refreshError)),
		);
	}
};

// Configure retry behavior
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

// Response interceptor with retry logic and token refresh
api.interceptors.response.use(
	(response: AxiosResponse) => {
		// Clean up from the pending requests map
		if (response.config.url) {
			const requestKey =
				response.config.url + JSON.stringify(response.config.params ?? {});
			pendingRequests.delete(requestKey);
		}

		// For malformed JSON
		if (
			response.headers["content-type"]?.includes("application/json") &&
			typeof response.data === "string"
		) {
			try {
				JSON.parse(response.data);
			} catch (error) {
				return Promise.reject(
					new Error(`Malformed JSON in response: ${error}`),
				);
			}
		}

		return response;
	},
	async (error) => {
		// Clean up from the pending requests map
		if (error.config?.url) {
			const requestKey =
				error.config.url + JSON.stringify(error.config.params ?? {});
			pendingRequests.delete(requestKey);
		}

		const originalRequest = error.config;

		// Do not log or retry if the request was canceled
		if (axios.isCancel(error)) {
			const message =
				typeof error === "object" && error
					? JSON.stringify(error)
					: String(error);
			const cancelError = error instanceof Error ? error : new Error(message);
			return Promise.reject(cancelError);
		}

		if (shouldRetryRequest(error)) {
			return handleRequestRetry(error);
		}

		if (error.response?.status === 401 && !originalRequest?._retry) {
			return handleTokenRefresh(error);
		}

		// Log other errors to monitoring
		if (error.response?.status !== 401 && !axios.isCancel(error)) {
			errorMonitor.captureException(error, {
				url: error.config?.url,
				method: error.config?.method,
				status: error.response?.status,
			});
		}

		return Promise.reject(
			error instanceof Error ? error : new Error(String(error)),
		);
	},
);

export default api;
