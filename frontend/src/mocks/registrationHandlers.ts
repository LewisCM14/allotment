import type { ITokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";

interface IRegisterRequest {
	user_email: string;
	user_password: string;
	user_first_name: string;
	user_country_code: string;
}

export const registrationHandlers = [
	// Mock the registration endpoint
	http.post(buildUrl("/registration"), async ({ request }) => {
		const body = (await request.json()) as IRegisterRequest;

		// Check for existing email scenario
		if (body?.user_email === "exists@example.com") {
			return jsonError("Email already registered", 409);
		}

		if (body?.user_email === "bad@example.com") {
			return jsonError("Bad request data", 400);
		}

		// Successful registration
		return jsonOk({
			access_token: "new-access-token",
			refresh_token: "new-refresh-token",
			token_type: "bearer",
			user_first_name: body.user_first_name,
			is_email_verified: false,
			user_id: "user-new-id",
		});
	}),
	http.options(buildUrl("/registration"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the email verification endpoint (during registration flow)
	http.post(
		buildUrl("/registration/email-verifications/:token"),
		async ({ params, request }) => {
			const token = params.token;
			const url = new URL(request.url);
			const fromReset = url.searchParams.get("fromReset") === "true";

			if (token === "valid-token") {
				if (fromReset) {
					return jsonOk({
						message:
							"Email verified successfully. You can now reset your password.",
					});
				}
				return jsonOk({ message: "Email verified successfully" });
			}

			if (token === "reset-token") {
				return jsonOk({
					message:
						"Email verified successfully. You can now reset your password.",
				});
			}

			if (token === "invalid-token") {
				return jsonError("Invalid or expired verification token", 400);
			}

			if (token === "expired-token") {
				return jsonError("Verification token has expired", 400);
			}

			return jsonError("Token not handled", 400);
		},
	),
	http.options(buildUrl("/registration/email-verifications/:token"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
