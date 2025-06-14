import type {
	ILoginRequest,
	ILoginResponse,
	IRegisterRequest,
} from "@/features/user/services/UserService";
import { AUTH_ERRORS } from "@/features/user/services/UserService";
import type { IRefreshRequest } from "@/services/api";
import { API_URL, API_VERSION } from "@/services/apiConfig";
import type { ITokenPair } from "@/store/auth/AuthContext";
import { http, HttpResponse } from "msw";

interface IPasswordResetRequest {
	user_email: string;
}

interface IPasswordResetAction {
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
		const body = (await request.json()) as IPasswordResetRequest;
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

const familyHandlers = [
	// Mock the botanical groups endpoint
	http.get(buildUrl("/families/botanical-groups/"), ({ request }) => {
		const url = new URL(request.url);

		if (url.searchParams.get("abort") === "true") {
			return HttpResponse.json(
				{ detail: "Request cancelled" },
				{ status: 499 },
			);
		}

		// Successful response
		return HttpResponse.json([
			{
				id: "group-1",
				name: "Brassicaceae",
				recommended_rotation_years: 3,
				families: [
					{ id: "family-1", name: "Cabbage" },
					{ id: "family-2", name: "Broccoli" },
				],
			},
			{
				id: "group-2",
				name: "Solanaceae",
				recommended_rotation_years: 4,
				families: [
					{ id: "family-3", name: "Tomatoes" },
					{ id: "family-4", name: "Potatoes" },
				],
			},
			{
				id: "group-3",
				name: "Leguminosae",
				recommended_rotation_years: null,
				families: [
					{ id: "family-5", name: "Peas" },
					{ id: "family-6", name: "Beans" },
				],
			},
		]);
	}),

	http.options(buildUrl("/families/botanical-groups/"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Add handler for family details route
	http.get(buildUrl("/families/:familyId/"), ({ params }) => {
		const { familyId } = params;
		if (familyId === "family-1") {
			return HttpResponse.json({
				id: "family-1",
				name: "Cabbage",
				botanical_group: "Brassicaceae",
				recommended_rotation_years: 3,
				companion_families: ["Beans", "Peas"],
				antagonist_families: ["Tomatoes"],
				common_pests: [
					{ name: "Cabbage White Butterfly", treatment: "Netting" },
				],
				common_diseases: [
					{
						name: "Clubroot",
						symptoms: "Swollen roots",
						treatment: "Lime soil",
						prevention: "Crop rotation",
					},
				],
			});
		}
		if (familyId === "family-404") {
			return new HttpResponse(JSON.stringify({ detail: "Family not found" }), {
				status: 404,
				headers: { "Content-Type": "application/json" },
			});
		}
		// Default mock for other families
		return HttpResponse.json({
			id: familyId,
			name: "Unknown Family",
			botanical_group: "Unknown",
			recommended_rotation_years: null,
			companion_families: [],
			antagonist_families: [],
			common_pests: [],
			common_diseases: [],
		});
	}),
	http.options(buildUrl("/families/:familyId/"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];

export const handlers = [...authHandlers, ...userHandlers, ...familyHandlers];
