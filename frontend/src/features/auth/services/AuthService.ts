import type { ITokenPair } from "@/store/auth/AuthContext";
import { tokenStore } from "@/services/tokenStore";
import api, { handleApiError } from "../../../services/api";

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

		tokenStore.setTokens({ access_token, refresh_token });

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
		return handleApiError(
			error,
			"Invalid email or password. Please try again.",
		);
	}
};

export interface IRefreshTokenRequest {
	refresh_token: string;
}

export const refreshAccessToken = async (): Promise<ITokenPair> => {
	try {
		const refreshToken = tokenStore.getRefreshToken();
		if (!refreshToken) {
			throw new Error("No refresh token available");
		}

		const response = await api.post<ITokenPair>("/auth/token/refresh", {
			refresh_token: refreshToken,
		});

		tokenStore.setTokens(response.data);

		return response.data;
	} catch (error: unknown) {
		// Clear tokens on refresh failure
		tokenStore.clearTokens();

		return handleApiError(error, "Failed to refresh authentication token");
	}
};

export const requestPasswordReset = async (
	email: string,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			"/auth/password-resets",
			{ user_email: email },
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(
			error,
			"Password reset failed. Please try again later.",
		);
	}
};

export const resetPassword = async (
	token: string,
	newPassword: string,
): Promise<{ message: string }> => {
	try {
		const response = await api.post<{ message: string }>(
			"/auth/password-resets/confirm",
			{ token, new_password: newPassword },
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to reset password");
	}
};
