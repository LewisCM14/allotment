import type {
	ILoginRequest,
	ILoginResponse,
} from "@/features/auth/services/AuthService";
import type { IRefreshRequest } from "@/services/api";
import type { ITokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";

interface IPasswordResetRequest {
	user_email: string;
}

interface IPasswordResetAction {
	token: string;
	new_password: string;
}

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

	// Mock password reset request endpoint
	http.post(buildUrl("/auth/password-resets"), async ({ request }) => {
		const body = (await request.json()) as IPasswordResetRequest;
		const email = body.user_email;

		if (email === "nonexistent@example.com") {
			return jsonError("Email address not found", 404);
		}
		if (email === "unverified@example.com") {
			return jsonOk({
				message:
					"Your email is not verified. A verification email has been sent to your address.",
			});
		}
		if (email === "invalid-email") {
			return jsonError("Invalid email format", 400);
		}

		return jsonOk({
			message:
				"If your email exists in our system and is verified, you will receive a password reset link shortly.",
		});
	}),
	http.options(buildUrl("/auth/password-resets"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock password reset action endpoint
	http.post(
		buildUrl("/auth/password-resets/:token"),
		async ({ params, request }) => {
			const body = (await request.json()) as IPasswordResetAction;
			const token = params.token;

			if (token === "invalid-token") {
				return jsonError("Invalid or expired reset token", 401);
			}

			if (token === "expired-token") {
				return jsonError(
					JSON.stringify([
						{ msg: "Reset token has expired", type: "token_expired_error" },
					]),
					400,
				);
			}

			if (token === "valid-token" && body.new_password === "weak") {
				return jsonError("Password must be at least 8 characters long", 400);
			}

			if (token === "valid-reset-token" || token === "valid-token") {
				return jsonOk({ message: "Password reset successfully" });
			}

			return jsonError("Token not handled for reset", 400);
		},
	),
	http.options(buildUrl("/auth/password-resets/:token"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
