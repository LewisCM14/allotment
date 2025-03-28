import axios from "axios";

export interface IApiError {
	detail: string;
	status_code?: number;
}

export const handleApiError = (
	error: unknown,
	defaultMessage = "Operation failed",
): never => {
	if (axios.isAxiosError(error)) {
		const apiError = error.response?.data as IApiError;
		console.error("API Error:", {
			status: error.response?.status,
			data: apiError,
			url: error.config?.url,
		});

		if (error.response?.status === 422) {
			const validationErrors = apiError.detail;
			const errorMessage = Array.isArray(validationErrors)
				? validationErrors.map((err) => err.msg).join(", ")
				: "Invalid input data";
			throw new Error(errorMessage);
		}

		throw new Error(apiError?.detail || defaultMessage);
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
		const token = localStorage.getItem("token");
		if (token) config.headers.Authorization = `Bearer ${token}`;
		return config;
	},
	(error) => {
		return Promise.reject(error);
	},
);

export default api;
