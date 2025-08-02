import api, { handleApiError } from "../../../services/api";

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
		return handleApiError(
			error,
			"Email verification failed. Please request a new verification link.",
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
		return handleApiError(
			error,
			"Failed to fetch verification status. Please try again.",
		);
	}
};
