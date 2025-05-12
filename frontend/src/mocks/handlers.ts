import type {
	ILoginRequest,
	ILoginResponse,
	IRegisterRequest,
} from "@/features/user/UserService";
import type { IRefreshRequest } from "@/services/api";
import type { TokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";

interface PasswordResetRequest {
	user_email: string;
}

interface PasswordResetAction {
	token: string;
	new_password: string;
}

export const handlers = [
	// Mock the login endpoint
	http.post("/user/auth/login", async ({ request }) => {
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
				is_email_verified: true,
				user_id: "user-123",
			} as ILoginResponse);
		}

		// Return 401 for invalid credentials
		return new HttpResponse(
			JSON.stringify({ detail: "Invalid email or password" }),
			{
				status: 401,
				headers: { "Content-Type": "application/json" },
			},
		);
	}),

	// Mock the registration endpoint
	http.post("/user", async ({ request }) => {
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
	http.post("/user/auth/refresh", async ({ request }) => {
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
	}),

	// Mock the requestVerificationEmail endpoint
	http.post("/user/send-verification-email", async ({ request }) => {
		const url = new URL(request.url);
		const email = url.searchParams.get("user_email");

		if (email === "test@example.com") {
			return HttpResponse.json({ message: "Verification email sent" });
		}

		if (email === "nonexistent@example.com") {
			return new HttpResponse(
				JSON.stringify({ detail: "Email address not found" }),
				{
					status: 404,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return new HttpResponse(null, { status: 400 });
	}),

	// Mock the Verify Email endpoint
	http.get("/user/verify-email", async ({ request }) => {
		const url = new URL(request.url);
		const token = url.searchParams.get("token");

		if (token === "valid-token") {
			return HttpResponse.json({ message: "Email verified successfully" });
		}

		if (token === "invalid-token") {
			return new HttpResponse(
				JSON.stringify({ detail: "Invalid verification token" }),
				{
					status: 400,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		if (token === "expired-token") {
			return new HttpResponse(JSON.stringify({ detail: "Token has expired" }), {
				status: 410,
				headers: { "Content-Type": "application/json" },
			});
		}

		return new HttpResponse(null, { status: 400 });
	}),

	http.post("/user/request-password-reset", async ({ request }) => {
		const body = (await request.json()) as PasswordResetRequest;
		const email = body.user_email;

		if (email === "nonexistent@example.com") {
			return new HttpResponse(
				JSON.stringify({ detail: "Email address not found" }),
				{
					status: 404,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return HttpResponse.json({ message: "Reset email sent" });
	}),

	http.post("/user/reset-password", async ({ request }) => {
		const body = (await request.json()) as PasswordResetAction;
		const token = body.token;

		if (token === "invalid-token") {
			return new HttpResponse(
				JSON.stringify({ detail: "Invalid or expired token" }),
				{
					status: 400,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		if (token === "validation-error") {
			return new HttpResponse(
				JSON.stringify({
					detail: [
						{
							loc: ["body", "new_password"],
							msg: "Password too short",
						},
					],
				}),
				{
					status: 422,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return HttpResponse.json({ message: "Password updated" });
	}),
];
