import type { ITokenPair } from "@/store/auth/AuthContext";
import { formatError } from "@/utils/errorUtils";
import api, { handleApiError } from "../../../services/api";
import axios from "axios";

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

// Custom error for when no allotment exists (404)
export class NoAllotmentFoundError extends Error {
	constructor(message = "No allotment found") {
		super(message);
		this.name = "NoAllotmentFoundError";
	}
}

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
			firstName: firstName ?? "User",
			userData: {
				user_email: email,
				user_id: user_id ?? "",
				is_email_verified: is_email_verified ?? false,
			},
		};
	} catch (error: unknown) {
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
	} catch (error: unknown) {
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
	} catch (error: unknown) {
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
	} catch (error: unknown) {
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
	} catch (error: unknown) {
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
	} catch (error: unknown) {
		return handleApiError(error, AUTH_ERRORS.FETCH_VERIFICATION_STATUS_FAILED);
	}
};

export interface IAllotmentRequest {
	allotment_postal_zip_code: string;
	allotment_width_meters: number;
	allotment_length_meters: number;
}

export interface IAllotmentUpdateRequest {
	allotment_postal_zip_code?: string;
	allotment_width_meters?: number;
	allotment_length_meters?: number;
}

export interface IAllotmentResponse {
	user_allotment_id: string; // UUID as string from backend
	user_id: string; // UUID as string from backend
	allotment_postal_zip_code: string;
	allotment_width_meters: number; // Compatible with backend float
	allotment_length_meters: number; // Compatible with backend float
}

export const createUserAllotment = async (
	allotmentData: IAllotmentRequest,
): Promise<IAllotmentResponse> => {
	try {
		const response = await api.post<IAllotmentResponse>(
			"/users/allotment",
			allotmentData,
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(
			error,
			"Failed to create allotment. Please try again.",
		);
	}
};

export const getUserAllotment = async (): Promise<IAllotmentResponse> => {
	try {
		// Use regular GET instead of cached GET since React Query handles caching
		const response = await api.get<IAllotmentResponse>("/users/allotment");
		return response.data;
	} catch (error: unknown) {
		if (axios.isAxiosError(error)) {
			if (!error.response) {
				return handleApiError(
					error,
					"Failed to fetch allotment. Please try again.",
				);
			}

			if (error.response.status === 404) {
				throw new NoAllotmentFoundError("No allotment found for this user");
			}
		}

		return handleApiError(
			error,
			"Failed to fetch allotment. Please try again.",
		);
	}
};

export const updateUserAllotment = async (
	allotmentData: IAllotmentUpdateRequest,
): Promise<IAllotmentResponse> => {
	try {
		const response = await api.put<IAllotmentResponse>(
			"/users/allotment",
			allotmentData,
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(
			error,
			"Failed to update allotment. Please try again.",
		);
	}
};

export interface IRefreshTokenRequest {
	refresh_token: string;
}

export const refreshAccessToken = async (): Promise<ITokenPair> => {
	try {
		const refreshToken = localStorage.getItem("refresh_token");
		if (!refreshToken) {
			throw new Error("No refresh token available");
		}

		const response = await api.post<ITokenPair>("/auth/token/refresh", {
			refresh_token: refreshToken,
		});

		// Update stored tokens
		localStorage.setItem("access_token", response.data.access_token);
		localStorage.setItem("refresh_token", response.data.refresh_token);

		return response.data;
	} catch (error: unknown) {
		// Clear tokens on refresh failure
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");

		return handleApiError(error, "Failed to refresh authentication token");
	}
};
