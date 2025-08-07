import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";

const mockUserProfile = {
	user_id: "123e4567-e89b-12d3-a456-426614174000",
	user_email: "test@example.com",
	user_first_name: "Testy",
	user_country_code: "GB",
	is_email_verified: false,
};

export const userHandlers = [
	// Mock the getUserProfile endpoint
	http.get(buildUrl("/users/profile"), async ({ request }) => {
		const authHeader = request.headers.get("authorization");

		if (!authHeader || !authHeader.startsWith("Bearer ")) {
			return jsonError("Unauthorized", 401);
		}

		return jsonOk(mockUserProfile);
	}),
	http.options(buildUrl("/users/profile"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock the updateUserProfile endpoint
	http.put(buildUrl("/users/profile"), async ({ request }) => {
		const body = (await request.json()) as {
			user_first_name?: string;
			user_country_code?: string;
		};

		if (!body.user_first_name || !body.user_country_code) {
			return jsonError("Invalid request data", 422);
		}

		// Update the mock profile with new data
		const updatedProfile = {
			...mockUserProfile,
			user_first_name: body.user_first_name,
			user_country_code: body.user_country_code,
		};

		return jsonOk(updatedProfile);
	}),
	http.options(buildUrl("/users/profile"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

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
