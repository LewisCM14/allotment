import type { TokenPair } from "@/store/auth/AuthContext";
import axios from "axios";
import api, { handleApiError } from "../../services/api";

interface IRegisterRequest {
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
		if (
			axios.isAxiosError(error) &&
			(error.response?.status === 409 || error.response?.status === 400)
		) {
			throw new Error(
				error.response?.data?.detail || "Email already registered",
			);
		}
		return handleApiError(error, "Registration failed");
	}
};

interface ILoginRequest {
	user_email: string;
	user_password: string;
}

export const loginUser = async (
	email: string,
	password: string,
): Promise<TokenPair> => {
	try {
		const requestData: ILoginRequest = {
			user_email: email,
			user_password: password,
		};

		const response = await api.post<TokenPair>(
			`${import.meta.env.VITE_API_VERSION}/user/auth/login`,
			requestData,
		);
		return response.data;
	} catch (error) {
		return handleApiError(error, "Login failed");
	}
};
