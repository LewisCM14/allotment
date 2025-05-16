import type {
	ILoginRequest,
	ILoginResponse,
	IRegisterRequest,
} from "@/features/user/UserService";
import { AUTH_ERRORS } from "@/features/user/UserService";
import type { IRefreshRequest } from "@/services/api";
import { API_URL, API_VERSION } from "@/services/apiConfig";
import type { TokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";

interface PasswordResetRequest {
	user_email: string;
}

interface PasswordResetAction {
	token: string;
	new_password: string;
}

// Helper to construct full URLs for handlers
export const buildUrl = (path: string) => {
	const normalizedPath =
		API_VERSION.endsWith("/") || path.startsWith("/") ? path : `/${path}`;
	return `${API_URL}${API_VERSION}${normalizedPath}`
		.replace(/\/\//g, "/")
		.replace(/^http:\//, "http://")
		.replace(/^https:\//, "https://");
};

export const handlers = [
	// Mock the login endpoint
	http.post(buildUrl("/user/auth/login"), async ({ request }) => {
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
	http.options(buildUrl("/user/auth/login"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the registration endpoint
	http.post(buildUrl("/user"), async ({ request }) => {
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
	http.options(buildUrl("/user"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the token refresh endpoint
	http.post(buildUrl("/user/auth/refresh"), async ({ request }) => {
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
	http.options(buildUrl("/user/auth/refresh"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the requestVerificationEmail endpoint
	http.post(buildUrl("/user/send-verification-email"), async ({ request }) => {
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
	http.options(buildUrl("/user/send-verification-email"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the Verify Email endpoint
	http.get(buildUrl("/user/verify-email"), async ({ request }) => {
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
			return new HttpResponse(
				JSON.stringify({ detail: AUTH_ERRORS.VERIFICATION_TOKEN_EXPIRED }),
				{
					status: 410,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return new HttpResponse(null, { status: 400 });
	}),
	// OPTIONS handler for GET is not strictly necessary but harmless
	http.options(buildUrl("/user/verify-email"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	http.post(buildUrl("/user/request-password-reset"), async ({ request }) => {
		const body = (await request.json()) as PasswordResetRequest;
		const email = body.user_email;

		if (email === "nonexistent@example.com") {
			return new HttpResponse(
				JSON.stringify({ detail: AUTH_ERRORS.EMAIL_NOT_FOUND }),
				{
					status: 404,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return HttpResponse.json({ message: "Reset email sent" });
	}),
	http.options(buildUrl("/user/request-password-reset"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	http.post(buildUrl("/user/reset-password"), async ({ request }) => {
		const body = (await request.json()) as PasswordResetAction;
		const token = body.token;

		if (token === "invalid-token") {
			return new HttpResponse(JSON.stringify({ detail: "Invalid token" }), {
				status: 400,
				headers: { "Content-Type": "application/json" },
			});
		}

		if (token === "validation-error") {
			return new HttpResponse(
				JSON.stringify({
					detail: [
						{
							loc: ["body", "new_password"],
							msg: "Too weak",
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
	http.options(buildUrl("/user/reset-password"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
