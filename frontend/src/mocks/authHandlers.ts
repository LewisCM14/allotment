import type {
	ILoginRequest,
	ILoginResponse,
} from "@/features/auth/services/AuthService";
import type { IRefreshRequest } from "@/services/api";
import type { ITokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";

export const authHandlers = [
	// Mock the login endpoint
	http.post(buildUrl("/auth/token"), async ({ request }) => {
		const body = (await request.json()) as ILoginRequest;

		if (
			body?.user_email === "test@example.com" &&
			body?.user_password === "password123"
		) {
			return jsonOk({
				access_token: "mock-access-token",
				refresh_token: "mock-refresh-token",
				token_type: "bearer",
				user_first_name: "Test",
				is_email_verified: true,
				user_id: "user-123",
			} as ILoginResponse);
		}
		// Return 401 for invalid credentials
		return jsonError("Invalid email or password", 401);
	}),
	http.options(buildUrl("/auth/token"), () => {
		// Assuming /auth/token
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the token refresh endpoint
	http.post(buildUrl("/auth/token/refresh"), async ({ request }) => {
		const body = (await request.json()) as IRefreshRequest;

		if (body?.refresh_token === "mock-refresh-token") {
			return jsonOk({
				access_token: "refreshed-access-token",
				refresh_token: "new-refresh-token",
			} as ITokenPair);
		}
		return jsonError("Invalid refresh token", 401);
	}),
	http.options(buildUrl("/auth/token/refresh"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
