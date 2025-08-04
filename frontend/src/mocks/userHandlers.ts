import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";

export const userHandlers = [
	// Mock the requestVerificationEmail endpoint (user profile operations)
	http.post(buildUrl("/users/email-verifications"), async ({ request }) => {
		const body = (await request.json()) as { user_email?: string };
		const email = body?.user_email;

		if (email === "test@example.com") {
			return jsonOk({ message: "Verification email sent" });
		}

		if (email === "nonexistent@example.com") {
			return jsonError("Email address not found", 404);
		}

		return new HttpResponse(null, { status: 400 });
	}),
	http.options(buildUrl("/users/email-verifications"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the verification status endpoint
	http.get(buildUrl("/users/verification-status"), ({ request }) => {
		const url = new URL(request.url);
		const email = url.searchParams.get("user_email");

		if (email === "verified@example.com") {
			return jsonOk({
				is_email_verified: true,
				user_id: "user-verified",
			});
		}
		if (email === "notverified@example.com") {
			return jsonOk({
				is_email_verified: false,
				user_id: "user-not-verified",
			});
		}
		if (email === "unknown@example.com") {
			return jsonError("User not found", 404);
		}
		if (email === "server-error@example.com") {
			return jsonError("Internal server error", 500);
		}
		return jsonOk({
			is_email_verified: false,
			user_id: "user-default",
		});
	}),
	http.options(buildUrl("/users/verification-status"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
