import { AUTH_ERRORS } from "@/features/user/services/UserService";
import { apiCache } from "@/services/apiCache";
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

export const handleApiError = (
	error: unknown,
	defaultMessage: string,
): never => {
	if (axios.isAxiosError(error)) {
		if (!error.response) {
			throw new Error(AUTH_ERRORS.NETWORK_ERROR);
		}

		if (error.response.status === 401) {
			throw new Error(AUTH_ERRORS.INVALID_CREDENTIALS);
		}

		if (error.response.status === 500) {
			throw new Error(AUTH_ERRORS.SERVER_ERROR);
		}

		const errorDetail = error.response?.data?.detail;
		if (errorDetail) {
			throw new Error(
				typeof errorDetail === "string"
					? errorDetail
					: JSON.stringify(errorDetail),
			);
		}
	}

	// Log to error monitoring
	errorMonitor.captureException(error, { defaultMessage });

	throw new Error(defaultMessage);
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

// Add custom methods to the api object
interface ApiExtensions {
	cachedGet: <T>(url: string, config?: AxiosRequestConfig) => Promise<T>;
}

// Extend the api type
const extendedApi = api as typeof api & ApiExtensions;

/**
 * Cached GET request implementation
 * Checks memory cache first, then makes network request if needed
 */
extendedApi.cachedGet = async <T>(
	url: string,
	config?: AxiosRequestConfig,
): Promise<T> => {
	// Create a unique cache key based on URL and params
	const cacheKey = `${url}:${JSON.stringify(config?.params || {})}`;

	// Try to get from cache first
	const cachedData = apiCache.get(cacheKey);
	if (cachedData) {
		return cachedData as T;
	}

	// If not in cache, make the request
	const response = await api.get<T>(url, config);

	// Store in cache
	apiCache.set(cacheKey, response.data);

	return response.data;
};

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
	const requestKey = config.url + JSON.stringify(config.params || {});

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
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
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
	originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

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

// Response interceptor with retry logic, token refresh, and cache management
api.interceptors.response.use(
	(response: AxiosResponse) => {
		// Clean up from the pending requests map
		if (response.config.url) {
			const requestKey =
				response.config.url + JSON.stringify(response.config.params || {});
			pendingRequests.delete(requestKey);
		}

		// Cache invalidation for mutation requests
		const { method, url: fullUrl } = response.config; // url here is the full URL
		if (
			method &&
			fullUrl &&
			["post", "put", "patch", "delete"].includes(method.toLowerCase())
		) {
			try {
				const pathName = new URL(fullUrl).pathname;

				let resourcePath = pathName;
				if (API_VERSION && pathName.startsWith(API_VERSION)) {
					resourcePath = pathName.substring(API_VERSION.length);
				}
				resourcePath = resourcePath.startsWith("/")
					? resourcePath.substring(1)
					: resourcePath;

				const resourceParts = resourcePath.split("/");
				if (resourceParts.length > 0) {
					const resourceType = resourceParts[0];
					apiCache.invalidateByPrefix(`/${resourceType}`);
				}
			} catch (e) {
				// Log error if URL parsing or cache invalidation fails
				errorMonitor.captureException(e, { context: "cache_invalidation" });
			}
		}

		return response;
	},
	async (error) => {
		// Clean up from the pending requests map
		if (error.config?.url) {
			const requestKey =
				error.config.url + JSON.stringify(error.config.params || {});
			pendingRequests.delete(requestKey);
		}

		const originalRequest = error.config;

		// Do not log or retry if the request was canceled
		if (axios.isCancel(error)) {
			return Promise.reject(
				error instanceof Error
					? error
					: new Error(
							typeof error === "object" ? JSON.stringify(error) : String(error),
						),
			);
		}

		if (shouldRetryRequest(error)) {
			return handleRequestRetry(error);
		}

		if (error.response?.status === 401 && !originalRequest?._retry) {
			return handleTokenRefresh(error);
		}

		// Log other errors to monitoring
		if (error.response?.status !== 401 && !axios.isCancel(error)) {
			// Added !axios.isCancel(error) here too for safety
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

export default extendedApi;
