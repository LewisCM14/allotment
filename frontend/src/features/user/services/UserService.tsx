import api, { handleApiError } from "../../../services/api";
import { errorMonitor } from "../../../services/errorMonitoring";

export interface UserProfile {
	user_id: string;
	user_email: string;
	user_first_name: string;
	user_country_code: string;
	is_email_verified: boolean;
	created_at: string;
	updated_at: string;
}

export interface UserProfileResponse {
	user_id: string;
	user_email: string;
	user_first_name: string;
	user_country_code: string;
	is_email_verified: boolean;
}

export interface UserProfileUpdate {
	user_first_name: string;
	user_country_code: string;
}

export const getUserProfile = async (): Promise<UserProfileResponse> => {
	try {
		const response = await api.get<UserProfileResponse>("/users/profile");
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getUserProfile",
			url: "/users/profile",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch user profile. Please try again.",
		);
	}
};

export const updateUserProfile = async (
	profileData: UserProfileUpdate,
): Promise<UserProfileResponse> => {
	try {
		const response = await api.put<UserProfileResponse>(
			"/users/profile",
			profileData,
		);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "updateUserProfile",
			url: "/users/profile",
			method: "PUT",
			data: profileData,
		});
		return handleApiError(
			error,
			"Failed to update user profile. Please try again.",
		);
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
		errorMonitor.captureException(error, {
			context: "checkEmailVerificationStatus",
			url: "/users/verification-status",
			method: "GET",
			email: email,
		});
		return handleApiError(
			error,
			"Failed to fetch verification status. Please try again.",
		);
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
		errorMonitor.captureException(error, {
			context: "requestVerificationEmail",
			url: "/users/email-verifications",
			method: "POST",
			email: email,
		});
		return handleApiError(error, "Failed to send verification email");
	}
};
