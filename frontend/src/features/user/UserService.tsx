import { formatError } from "@/lib/errorUtils";
import type { TokenPair } from "@/store/auth/AuthContext";
import axios from "axios";
import api, { handleApiError } from "../../services/api";

export const AUTH_ERRORS = {
	// Login specific errors
	INVALID_CREDENTIALS: "Invalid email or password. Please try again.",
	ACCOUNT_LOCKED: "Your account has been locked. Please contact support.",

	// Registration specific errors
	EMAIL_EXISTS: "This email is already registered. Try logging in instead.",
	REGISTRATION_FAILED: "Registration failed. Please try again.",

	// Common errors
	SERVER_ERROR: "Server error. Please try again later.",
	NETWORK_ERROR: "Network error. Please check your connection and try again.",
	UNKNOWN_ERROR: "An unexpected error occurred. Please try again.",

	// Use the common error formatter
	format: formatError,
};

export interface IRegisterRequest {
	user_email: string;
	user_password: string;
	user_first_name: string;
	user_country_code: string;
}

export const registerUser = async (
	email: string,
	password: string,
	firstName: string,
	countryCode: string,
): Promise<TokenPair> => {
	try {
		const requestData: IRegisterRequest = {
			user_email: email,
			user_password: password,
			user_first_name: firstName,
			user_country_code: countryCode,
		};

		const response = await api.post<TokenPair>(
			`${import.meta.env.VITE_API_VERSION}/user`,
			requestData,
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response?.status === 409) {
				throw new Error(AUTH_ERRORS.EMAIL_EXISTS);
			}
			if (error.response?.status === 400) {
				throw new Error(
					error.response?.data?.detail || AUTH_ERRORS.REGISTRATION_FAILED,
				);
			}
		}
		return handleApiError(error, AUTH_ERRORS.REGISTRATION_FAILED);
	}
};

export interface ILoginRequest {
	user_email: string;
	user_password: string;
}

export interface ILoginResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
	user_first_name?: string;
}

export const loginUser = async (
	email: string,
	password: string,
): Promise<{ tokens: TokenPair; firstName: string }> => {
	try {
		const requestData: ILoginRequest = {
			user_email: email,
			user_password: password,
		};

		const response = await api.post<ILoginResponse>(
			`${import.meta.env.VITE_API_VERSION}/user/auth/login`,
			requestData,
		);

		const { access_token, refresh_token, user_first_name } = response.data;

		localStorage.setItem("access_token", access_token);
		localStorage.setItem("refresh_token", refresh_token);

		let firstName = user_first_name;
		if (!firstName) {
			const emailName = email.split("@")[0].split(".")[0];
			firstName = emailName.charAt(0).toUpperCase() + emailName.slice(1);
		}

		return {
			tokens: {
				access_token,
				refresh_token,
			},
			firstName,
		};
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response?.status === 401) {
				throw new Error(AUTH_ERRORS.INVALID_CREDENTIALS);
			}
		}
		return handleApiError(error, AUTH_ERRORS.UNKNOWN_ERROR);
	}
};
