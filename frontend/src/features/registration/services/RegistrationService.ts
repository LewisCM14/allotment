import type { ITokenPair } from "@/store/auth/AuthContext";
import api, { handleApiError } from "../../../services/api";

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
		return handleApiError(error, "Registration failed. Please try again.");
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
		return handleApiError(
			error,
			"Email verification failed. Please request a new verification link.",
		);
	}
};
