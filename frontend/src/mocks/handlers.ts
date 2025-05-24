import type {
	ILoginRequest,
	ILoginResponse,
	IRegisterRequest,
} from "@/features/user/UserService";
import { AUTH_ERRORS } from "@/features/user/UserService";
import type { IRefreshRequest } from "@/services/api";
import { API_URL, API_VERSION } from "@/services/apiConfig";
import type { ITokenPair } from "@/store/auth/AuthContext";
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
	const apiVersionSegment = API_VERSION.startsWith("/")
		? API_VERSION
		: `/${API_VERSION}`;
	const pathSegment = path.startsWith("/") ? path : `/${path}`;
	return `${API_URL}${apiVersionSegment}${pathSegment}`.replace(
		/([^:]\/)\/+/g,
		"$1",
	);
};

const authHandlers = [
	// Mock the login endpoint
	http.post(buildUrl("/auth/token"), async ({ request }) => {
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
	http.options(buildUrl("/auth/token"), () => {
		// Assuming /auth/token
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the token refresh endpoint
	http.post(buildUrl("/auth/token/refresh"), async ({ request }) => {
		const body = (await request.json()) as IRefreshRequest;

		if (body?.refresh_token === "mock-refresh-token") {
			return HttpResponse.json({
				access_token: "refreshed-access-token",
				refresh_token: "new-refresh-token",
			} as ITokenPair);
		}

		return new HttpResponse(null, {
			status: 401,
			headers: { "Content-Type": "application/json" },
		});
	}),
	http.options(buildUrl("/auth/token/refresh"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];

const userHandlers = [
	// Mock the registration endpoint
	http.post(buildUrl("/users/"), async ({ request }) => {
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
		} as ITokenPair);
	}),
	http.options(buildUrl("/users/"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the requestVerificationEmail endpoint
	http.post(buildUrl("/users/email-verifications"), async ({ request }) => {
		const body = (await request.json()) as { user_email?: string };
		const email = body?.user_email;

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
	http.options(buildUrl("/users/email-verifications"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the Verify Email endpoint
	http.post(
		buildUrl("/users/email-verifications/:token"),
		async ({ params, request }) => {
			const token = params.token;
			const url = new URL(request.url);
			const fromReset = url.searchParams.get("fromReset") === "true";

			if (token === "valid-token") {
				return HttpResponse.json({
					message: `Email verified successfully${fromReset ? ". You can now reset your password." : ""}`,
				});
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

			return new HttpResponse(JSON.stringify({ detail: "Token not handled" }), {
				status: 400,
			});
		},
	),
	http.options(buildUrl("/users/email-verifications/:token"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	http.post(buildUrl("/users/password-resets"), async ({ request }) => {
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
		if (email === "unverified@example.com") {
			return new HttpResponse(
				JSON.stringify({
					detail: "Email not verified. Please verify your email first.",
				}),
				{
					status: 400,
					headers: { "Content-Type": "application/json" },
				},
			);
		}

		return HttpResponse.json({ message: "Reset email sent" });
	}),
	http.options(buildUrl("/users/password-resets"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	http.post(
		buildUrl("/users/password-resets/:token"),
		async ({ params, request }) => {
			const body = (await request.json()) as PasswordResetAction;
			const token = params.token;

			if (token === "invalid-token") {
				return new HttpResponse(
					JSON.stringify({ detail: "Invalid or expired token" }),
					{
						status: 400,
						headers: { "Content-Type": "application/json" },
					},
				);
			}

			if (token === "validation-error-token" && body.new_password === "weak") {
				return new HttpResponse(
					JSON.stringify({
						detail: [
							{
								loc: ["body", "new_password"],
								msg: "Invalid password format",
							},
						],
					}),
					{
						status: 422,
						headers: { "Content-Type": "application/json" },
					},
				);
			}
			if (token === "valid-token") {
				return HttpResponse.json({ message: "Password updated" });
			}
			return new HttpResponse(
				JSON.stringify({ detail: "Token not handled for reset" }),
				{ status: 400 },
			);
		},
	),
	http.options(buildUrl("/users/password-resets/:token"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	http.get(buildUrl("/users/verification-status"), ({ request }) => {
		const url = new URL(request.url);
		const email = url.searchParams.get("user_email");

		if (email === "verified@example.com") {
			return HttpResponse.json({
				is_email_verified: true,
				user_id: "user-verified",
			});
		}
		if (email === "notverified@example.com") {
			return HttpResponse.json({
				is_email_verified: false,
				user_id: "user-not-verified",
			});
		}
		if (email === "unknown@example.com") {
			return HttpResponse.json({ detail: "User not found" }, { status: 404 });
		}
		return HttpResponse.json({
			is_email_verified: false,
			user_id: "user-default",
		});
	}),
	http.options(buildUrl("/users/verification-status"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];

export const handlers = [
	...authHandlers,
	...userHandlers,
	// ...other groups of handlers
];
