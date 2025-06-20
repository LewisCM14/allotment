import type { ITokenPair } from "@/store/auth/AuthContext";
import { formatError } from "@/utils/errorUtils";
import axios from "axios";
import api, { handleApiError } from "../../../services/api";

export const AUTH_ERRORS = {
	// Login specific errors
	INVALID_CREDENTIALS: "Invalid email or password. Please try again.",
	ACCOUNT_LOCKED: "Your account has been locked. Please contact support.",

	// Registration specific errors
	EMAIL_EXISTS: "This email is already registered. Try logging in instead.",
	REGISTRATION_FAILED: "Registration failed. Please try again.",

	// Password reset specific errors
	EMAIL_NOT_FOUND: "Email address not found. Please check and try again.",
	EMAIL_NOT_VERIFIED:
		"Your email is not verified. A verification link has been sent.",
	RESET_FAILED: "Password reset failed. Please try again later.",

	// Email verification errors
	VERIFICATION_FAILED:
		"Email verification failed. Please request a new verification link.",
	VERIFICATION_TOKEN_EXPIRED:
		"The verification link has expired. Please request a new one.",
	VERIFICATION_TOKEN_INVALID:
		"Invalid verification link. Please request a new one.",

	// Common errors
	SERVER_ERROR: "Server error. Please try again later.",
	NETWORK_ERROR: "Network error. Please check your connection and try again.",
	UNKNOWN_ERROR: "An unexpected error occurred. Please try again.",

	// Email verification status specific error
	FETCH_VERIFICATION_STATUS_FAILED:
		"Failed to fetch verification status. Please try again.",

	// Use the common error formatter
	format: formatError,
};

export interface IRegisterRequest {
	user_email: string;
	user_password: string;
	user_first_name: string;
	user_country_code: string;
}

interface IValidationErrorDetail {
	msg?: string;
	loc?: string[];
	type?: string;
}

// Helper function to format validation errors from the API
const formatValidationErrors = (
	details: IValidationErrorDetail[] | unknown,
): string => {
	if (!details || !Array.isArray(details)) return "";

	try {
		const messages = details
			.map((err: IValidationErrorDetail) => err.msg || "Validation error")
			.join(", ");
		return messages || "Validation failed. Please check your inputs.";
	} catch (e) {
		return "Validation failed. Please check your inputs.";
	}
};

export const registerUser = async (
	email: string,
	password: string,
	firstName: string,
	countryCode: string,
): Promise<ITokenPair> => {
	try {
		const requestData: IRegisterRequest = {
			user_email: email,
			user_password: password,
			user_first_name: firstName,
			user_country_code: countryCode,
		};

		const response = await api.post<ITokenPair>("/users/", requestData);
		return response.data;
	} catch (error: unknown) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 409:
						throw new Error(AUTH_ERRORS.EMAIL_EXISTS);
					case 400:
						throw new Error(
							formatError(error.response.data) ||
								AUTH_ERRORS.REGISTRATION_FAILED,
						);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								AUTH_ERRORS.REGISTRATION_FAILED,
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
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
	is_email_verified?: boolean;
	user_id?: string;
}

export interface IUserData {
	user_id: string;
	user_email: string;
	is_email_verified: boolean;
}

export const loginUser = async (
	email: string,
	password: string,
): Promise<{ tokens: ITokenPair; firstName: string; userData: IUserData }> => {
	try {
		const requestData: ILoginRequest = {
			user_email: email,
			user_password: password,
		};

		const response = await api.post<ILoginResponse>("/auth/token", requestData);

		const {
			access_token,
			refresh_token,
			user_first_name,
			is_email_verified,
			user_id,
		} = response.data;

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
			firstName: firstName || "User",
			userData: {
				user_email: email,
				user_id: user_id || "",
				is_email_verified: is_email_verified || false,
			},
		};
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 404:
						throw new Error("The email address you entered is not registered.");
					case 401:
						throw new Error(AUTH_ERRORS.INVALID_CREDENTIALS);
					case 403:
						throw new Error(AUTH_ERRORS.ACCOUNT_LOCKED);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								AUTH_ERRORS.INVALID_CREDENTIALS,
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
			}
		}
		return handleApiError(error, AUTH_ERRORS.UNKNOWN_ERROR);
	}
};

export const verifyEmail = async (
	token: string,
	fromReset = false,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			`/users/email-verifications/${token}`,
			null,
			{ params: { fromReset } },
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 400:
						throw new Error(
							formatError(error.response.data) ||
								AUTH_ERRORS.VERIFICATION_TOKEN_INVALID,
						);
					case 404:
						throw new Error(AUTH_ERRORS.VERIFICATION_TOKEN_INVALID);
					case 410:
						throw new Error(AUTH_ERRORS.VERIFICATION_TOKEN_EXPIRED);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								AUTH_ERRORS.VERIFICATION_FAILED,
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
			}
		}
		return handleApiError(error, AUTH_ERRORS.VERIFICATION_FAILED);
	}
};

export const requestVerificationEmail = async (
	email: string,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			"/users/email-verifications",
			{ user_email: email },
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 404:
						throw new Error(AUTH_ERRORS.EMAIL_NOT_FOUND);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								AUTH_ERRORS.VERIFICATION_FAILED,
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					case 503:
						throw new Error(
							"Email service is temporarily unavailable. Please try again later.",
						);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
			}
		}
		return handleApiError(error, "Failed to send verification email");
	}
};

export const requestPasswordReset = async (
	email: string,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			"/users/password-resets",
			{ user_email: email },
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 400:
						throw new Error(
							formatError(error.response.data) ||
								"Email not verified. Please verify your email first.",
						);
					case 404:
						throw new Error(AUTH_ERRORS.EMAIL_NOT_FOUND);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								AUTH_ERRORS.RESET_FAILED,
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					case 503:
						throw new Error(
							"Email service is temporarily unavailable. Please try again later.",
						);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
			}
		}
		return handleApiError(error, AUTH_ERRORS.RESET_FAILED);
	}
};

export const resetPassword = async (
	token: string,
	newPassword: string,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			`/users/password-resets/${token}`,
			{ new_password: newPassword },
		);
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 400:
						throw new Error(
							formatError(error.response.data) || "Invalid or expired token",
						);
					case 422:
						throw new Error(
							formatValidationErrors(error.response.data?.detail) ||
								"Invalid password format",
						);
					case 500:
						throw new Error(AUTH_ERRORS.SERVER_ERROR);
					default:
						throw new Error(
							formatError(error.response.data) || AUTH_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(AUTH_ERRORS.NETWORK_ERROR);
			}
		}
		return handleApiError(error, "Failed to reset password");
	}
};

export const checkEmailVerificationStatus = async (
	email: string,
): Promise<{ is_email_verified: boolean }> => {
	try {
		const response = await api.get<{ is_email_verified: boolean }>(
			"/users/verification-status",
			{
				params: { user_email: email },
			},
		);
		return response.data;
	} catch (error) {
		console.error("Error checking verification status:", error);
		if (axios.isAxiosError(error)) {
			if (error.response?.status === 404) {
				throw new Error(AUTH_ERRORS.EMAIL_NOT_FOUND);
			}
		}
		throw new Error(AUTH_ERRORS.FETCH_VERIFICATION_STATUS_FAILED);
	}
};
