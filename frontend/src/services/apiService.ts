/**
 * Unified API Service
 * Provides consistent methods for all API operations across the frontend
 * This is the recommended way to make API calls in the application
 */

import api, { handleApiError } from "./api";
import type { AxiosRequestConfig } from "axios";

interface ApiMethodOptions {
	/** Whether to use cached GET for read operations */
	useCache?: boolean;
	/** Custom error message for this specific operation */
	errorMessage?: string;
	/** Additional axios config */
	config?: AxiosRequestConfig;
}

/**
 * Unified API service with consistent error handling and caching patterns
 *
 * @example
 * // Simple GET request
 * const data = await apiService.get<UserData>("/users/profile");
 *
 * // GET with caching
 * const data = await apiService.get<AllotmentData>("/users/allotment", { useCache: true });
 *
 * // POST request
 * const result = await apiService.post<CreateResponse>("/users", userData);
 */
export class ApiService {
	/**
	 * GET request with optional caching
	 */
	async get<T>(url: string, options: ApiMethodOptions = {}): Promise<T> {
		const {
			useCache = false,
			errorMessage = "Failed to fetch data",
			config,
		} = options;

		try {
			if (useCache) {
				return await api.cachedGet<T>(url, config);
			}

			const response = await api.get<T>(url, config);
			return response.data;
		} catch (error: unknown) {
			return handleApiError(error, errorMessage);
		}
	}

	/**
	 * POST request for creating resources
	 */
	async post<T>(
		url: string,
		data: unknown,
		options: ApiMethodOptions = {},
	): Promise<T> {
		const { errorMessage = "Failed to create resource", config } = options;

		try {
			const response = await api.post<T>(url, data, config);
			return response.data;
		} catch (error: unknown) {
			return handleApiError(error, errorMessage);
		}
	}

	/**
	 * PUT request for updating resources
	 */
	async put<T>(
		url: string,
		data: unknown,
		options: ApiMethodOptions = {},
	): Promise<T> {
		const { errorMessage = "Failed to update resource", config } = options;

		try {
			const response = await api.put<T>(url, data, config);
			return response.data;
		} catch (error: unknown) {
			return handleApiError(error, errorMessage);
		}
	}

	/**
	 * PATCH request for partial updates
	 */
	async patch<T>(
		url: string,
		data: unknown,
		options: ApiMethodOptions = {},
	): Promise<T> {
		const { errorMessage = "Failed to update resource", config } = options;

		try {
			const response = await api.patch<T>(url, data, config);
			return response.data;
		} catch (error: unknown) {
			return handleApiError(error, errorMessage);
		}
	}

	/**
	 * DELETE request for removing resources
	 */
	async delete<T>(url: string, options: ApiMethodOptions = {}): Promise<T> {
		const { errorMessage = "Failed to delete resource", config } = options;

		try {
			const response = await api.delete<T>(url, config);
			return response.data;
		} catch (error: unknown) {
			return handleApiError(error, errorMessage);
		}
	}
}

// Export singleton instance - this is the main export to use
export const apiService = new ApiService();

// Also export the class for cases where you need multiple instances
export default apiService;
