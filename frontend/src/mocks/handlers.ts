import type {
	ILoginRequest,
	ILoginResponse,
	IRegisterRequest,
} from "@/features/user/UserService";
import type { IRefreshRequest } from "@/services/api";
import type { TokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";

const API_VERSION = import.meta.env?.VITE_API_VERSION || "/api/v1";
const API_URL = import.meta.env?.VITE_API_URL || "";

export const handlers = [
	// Mock the login endpoint
	http.post(`${API_URL}${API_VERSION}/user/auth/login`, async ({ request }) => {
		const body = (await request.json()) as ILoginRequest;

		// Example validation logic
		if (
			body?.user_email === "test@example.com" &&
			body?.user_password === "password123"
		) {
			return HttpResponse.json({
				access_token: "mock-access-token",
				refresh_token: "mock-refresh-token",
				token_type: "bearer",
				user_first_name: "Test",
			} as ILoginResponse);
		}

		// Return 401 for invalid credentials
		return new HttpResponse(null, {
			status: 401,
			statusText: "Unauthorized",
			headers: {
				"Content-Type": "application/json",
			},
		});
	}),

	// Mock the registration endpoint
	http.post(`${API_URL}${API_VERSION}/user`, async ({ request }) => {
		const body = (await request.json()) as IRegisterRequest;

		// Check for existing email scenario
		if (body?.user_email === "exists@example.com") {
			return new HttpResponse(
				JSON.stringify({ detail: "Email already registered" }),
				{
					status: 409,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		// Successful registration
		return HttpResponse.json({
			access_token: "new-access-token",
			refresh_token: "new-refresh-token",
		} as TokenPair);
	}),

	// Mock the token refresh endpoint
	http.post(
		`${API_URL}${API_VERSION}/user/auth/refresh`,
		async ({ request }) => {
			const body = (await request.json()) as IRefreshRequest;

			if (body?.refresh_token === "mock-refresh-token") {
				return HttpResponse.json({
					access_token: "refreshed-access-token",
					refresh_token: "new-refresh-token",
				} as TokenPair);
			}

			return new HttpResponse(null, {
				status: 401,
				headers: { "Content-Type": "application/json" },
			});
		},
	),
];
