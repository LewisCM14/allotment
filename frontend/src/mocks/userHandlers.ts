import type { IRegisterRequest } from "@/features/auth/services/RegistrationService";
import type { ITokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";

interface IPasswordResetRequest {
	user_email: string;
}

interface IPasswordResetAction {
	token: string;
	new_password: string;
}

export const userHandlers = [
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
					JSON.stringify({
						detail:
							"The verification link has expired. Please request a new one.",
					}),
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
		const body = (await request.json()) as IPasswordResetRequest;
		const email = body.user_email;

		if (email === "nonexistent@example.com") {
			return new HttpResponse(
				JSON.stringify({
					detail: "Email address not found. Please check and try again.",
				}),
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
			const body = (await request.json()) as IPasswordResetAction;
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
		if (email === "server-error@example.com") {
			return HttpResponse.json(
				{ detail: "Internal Server Error" },
				{ status: 500 },
			);
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
