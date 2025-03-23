import axios from "axios";
import api, { type ApiError } from "../../services/api";

interface LoginResponse {
	token: string;
}

interface LoginRequest {
	user_email: string;
	user_password: string;
}

export const loginUser = async (
	email: string,
	password: string,
): Promise<LoginResponse> => {
	try {
		const requestData: LoginRequest = {
			user_email: email,
			user_password: password,
		};

		const response = await api.post<LoginResponse>(
			`${import.meta.env.VITE_API_VERSION}/user/auth/login`,
			requestData,
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			const apiError = error.response?.data as ApiError;
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

			throw new Error(apiError?.detail || "Login failed");
		}
		throw error;
	}
};
