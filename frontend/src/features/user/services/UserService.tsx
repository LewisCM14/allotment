import api, { handleApiError } from "../../../services/api";

export interface UserProfile {
	user_id: string;
	user_email: string;
	user_first_name: string;
	user_country_code: string;
	is_email_verified: boolean;
	created_at: string;
	updated_at: string;
}

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
		return handleApiError(error, "Failed to send verification email");
	}
};
