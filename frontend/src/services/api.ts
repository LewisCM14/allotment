import { formatApiDetail } from "@/lib/errorUtils";
import type { TokenPair } from "@/store/auth/AuthContext";
import axios, { type AxiosError, type AxiosRequestConfig } from "axios";

export interface IApiError {
	detail: string | Array<{ msg: string; loc: string[] }>;
	status_code?: number;
}

const ERROR_MESSAGES = {
	401: "Invalid credentials. Please check your email and password.",
	403: "You don't have permission to perform this action.",
	404: "The requested resource was not found.",
	500: "Server error. Please try again later.",
};

const getErrorMessageByStatus = (
	status: number,
	apiError?: IApiError,
	defaultMessage = "Operation failed",
): string => {
	if (status in ERROR_MESSAGES) {
		return ERROR_MESSAGES[status as keyof typeof ERROR_MESSAGES];
	}

	if (status === 422 && apiError?.detail) {
		return formatApiDetail(apiError.detail);
	}

	if (status === 409) {
		return apiError?.detail
			? formatApiDetail(apiError.detail)
			: "A conflict occurred. This resource may already exist.";
	}

	return apiError?.detail ? formatApiDetail(apiError.detail) : defaultMessage;
};

export const handleApiError = (
	error: unknown,
	defaultMessage = "Operation failed",
): never => {
	if (axios.isAxiosError(error)) {
		const apiError = error.response?.data as IApiError;
		const status = error.response?.status || 0;

		console.error("API Error:", {
			status,
			data: apiError,
			url: error.config?.url,
		});

		const errorMessage = getErrorMessageByStatus(
			status,
			apiError,
			defaultMessage,
		);
		throw new Error(errorMessage);
	}
	throw error;
};

const api = axios.create({
	baseURL: `${import.meta.env.VITE_API_URL}`,
	headers: {
		"Content-Type": "application/json",
		Accept: "application/json",
	},
	withCredentials: true,
});

api.interceptors.request.use(
	(config) => {
		const token = localStorage.getItem("access_token");
		if (token) config.headers.Authorization = `Bearer ${token}`;
		return config;
	},
	(error) => {
		return Promise.reject(error);
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

const refreshAccessToken = async (): Promise<string | null> => {
	const refreshToken = localStorage.getItem("refresh_token");
	if (!refreshToken) return null;

	try {
		const response = await axios.post<TokenPair>(
			`${import.meta.env.VITE_API_URL}${import.meta.env.VITE_API_VERSION}/user/auth/refresh`,
			{ refresh_token: refreshToken },
			{ baseURL: "" }, // Use absolute URL
		);

		localStorage.setItem("access_token", response.data.access_token);
		localStorage.setItem("refresh_token", response.data.refresh_token);

		return response.data.access_token;
	} catch (error) {
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
		return null;
	}
};

// Response interceptor to handle token refresh
api.interceptors.response.use(
	(response) => response,
	async (error) => {
		const originalRequest = error.config;

		if (error.response?.status === 401 && !originalRequest._retry) {
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
				return Promise.reject(error);
			} catch (refreshError) {
				isRefreshing = false;
				processQueue(error, null);

				window.location.href = "/login";

				return Promise.reject(refreshError);
			}
		}

		return Promise.reject(error);
	},
);

export default api;
