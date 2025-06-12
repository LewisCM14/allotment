import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/handlers";
import { server } from "../../../mocks/server";
import * as apiModule from "../../../services/api";
import {
	AUTH_ERRORS,
	checkEmailVerificationStatus,
	loginUser,
	registerUser,
	requestPasswordReset,
	requestVerificationEmail,
	resetPassword,
	verifyEmail,
} from "./UserService";

describe("UserService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		localStorage.clear();
		vi.restoreAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("loginUser", () => {
		it("should log in a user with valid credentials", async () => {
			server.use(
				http.post(buildUrl("/auth/token"), async ({ request }) => {
					const body = (await request.json()) as { user_email?: string };
					if (body.user_email === "test@example.com") {
						return HttpResponse.json({
							access_token: "mock-access-token",
							refresh_token: "mock-refresh-token",
							token_type: "bearer",
							user_first_name: "Test",
							user_id: "user-123",
							is_email_verified: true,
						});
					}
					return HttpResponse.json(
						{ detail: "Unhandled mock case" },
						{ status: 500 },
					);
				}),
				http.options(buildUrl("/auth/token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);

			const result = await loginUser("test@example.com", "password123");

			expect(result).toEqual({
				tokens: {
					access_token: "mock-access-token",
					refresh_token: "mock-refresh-token",
				},
				firstName: "Test",
				userData: {
					user_email: "test@example.com",
					user_id: "user-123",
					is_email_verified: true,
				},
			});
			expect(localStorage.getItem("access_token")).toBe("mock-access-token");
			expect(localStorage.getItem("refresh_token")).toBe("mock-refresh-token");
		});

		it("should throw an error with invalid credentials", async () => {
			server.use(
				http.post(buildUrl("/auth/token"), async ({ request }) => {
					const body = (await request.json()) as { user_email?: string };
					if (body.user_email === "wrong@example.com") {
						return HttpResponse.json(
							{ detail: "Invalid email or password" },
							{ status: 401 },
						);
					}
					return HttpResponse.json(
						{ detail: "Unhandled mock case" },
						{ status: 500 },
					);
				}),
				http.options(buildUrl("/auth/token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(loginUser("wrong@example.com", "wrong")).rejects.toThrow(
				AUTH_ERRORS.INVALID_CREDENTIALS,
			);
		});

		it("should throw an error for user not found (404)", async () => {
			server.use(
				http.post(buildUrl("/auth/token"), () => {
					return HttpResponse.json(
						{ detail: "User not found" },
						{ status: 404 },
					);
				}),
			);
			await expect(
				loginUser("notfound@example.com", "password"),
			).rejects.toThrow("The email address you entered is not registered.");
		});

		it("should throw an error for account locked (403)", async () => {
			server.use(
				http.post(buildUrl("/auth/token"), () => {
					return HttpResponse.json(
						{ detail: "Account locked" },
						{ status: 403 },
					);
				}),
			);
			await expect(loginUser("locked@example.com", "password")).rejects.toThrow(
				AUTH_ERRORS.ACCOUNT_LOCKED,
			);
		});

		it("should throw an error for validation error (422)", async () => {
			server.use(
				http.post(buildUrl("/auth/token"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Invalid input" }] },
						{ status: 422 },
					);
				}),
			);
			await expect(
				loginUser("badinput@example.com", "password"),
			).rejects.toThrow("Invalid input");
		});

		it("should handle unexpected server responses", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");

			const serverError = new Error("Server returned unexpected response");
			Object.defineProperty(serverError, "isAxiosError", { value: true });
			Object.defineProperty(serverError, "response", {
				value: {
					status: 500,
					data: "Unexpected response",
				},
			});

			postSpy.mockRejectedValueOnce(serverError);

			await expect(
				loginUser("test@example.com", "password123"),
			).rejects.toThrow(AUTH_ERRORS.SERVER_ERROR);

			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");

			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "response", { value: undefined });
			Object.defineProperty(networkError, "request", { value: {} });

			postSpy.mockRejectedValueOnce(networkError);

			await expect(
				loginUser("test@example.com", "password123"),
			).rejects.toThrow(/Network error/i);

			postSpy.mockRestore();
		});
	});

	describe("registerUser", () => {
		it("should register a new user successfully", async () => {
			const mockApiResponse = {
				access_token: "new-access-token",
				refresh_token: "new-refresh-token",
				token_type: "bearer",
				user_first_name: "John",
				is_email_verified: false,
				user_id: "user-new-id",
			};
			server.use(
				http.post(buildUrl("/users/"), () => {
					return HttpResponse.json(mockApiResponse);
				}),
				http.options(buildUrl("/users/"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);

			const result = await registerUser(
				"new@example.com",
				"password123",
				"John",
				"US",
			);

			expect(result).toEqual(mockApiResponse);
		});

		it("should throw an error if email already exists (409)", async () => {
			server.use(
				http.post(buildUrl("/users/"), () => {
					return HttpResponse.json(
						{ detail: "Email already registered" },
						{ status: 409 },
					);
				}),
				http.options(buildUrl("/users/"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);

			await expect(
				registerUser("exists@example.com", "password123", "John", "US"),
			).rejects.toThrow(AUTH_ERRORS.EMAIL_EXISTS);
		});

		it("should handle bad request errors (400)", async () => {
			server.use(
				http.post(buildUrl("/users/"), () => {
					return HttpResponse.json(
						{ detail: "Bad request data" },
						{ status: 400 },
					);
				}),
				http.options(buildUrl("/users/"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				registerUser("bad@example.com", "password", "Bad", "XX"),
			).rejects.toThrow("Bad request data");
		});

		it("should handle validation errors from the server (422)", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const validationError = new Error("Request failed with status code 422");
			Object.defineProperty(validationError, "isAxiosError", { value: true });
			Object.defineProperty(validationError, "response", {
				value: {
					status: 422,
					data: {
						detail: [
							{
								loc: ["body", "user_password"],
								msg: "Password must be at least 8 characters",
								type: "value_error",
							},
						],
					},
				},
			});

			postSpy.mockRejectedValueOnce(validationError);

			await expect(
				registerUser("valid@example.com", "short", "John", "US"),
			).rejects.toThrow(/Password must be at least 8 characters/);

			postSpy.mockRestore();
		});
	});

	describe("requestVerificationEmail", () => {
		it("should send a verification email successfully", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications"),
					async ({ request }) => {
						const body = (await request.json()) as { user_email?: string };
						if (body.user_email === "test@example.com") {
							return HttpResponse.json({ message: "Verification email sent" });
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			const result = await requestVerificationEmail("test@example.com");
			expect(result).toEqual({ message: "Verification email sent" });
		});

		it("should handle email not found error (404)", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications"),
					async ({ request }) => {
						const body = (await request.json()) as { user_email?: string };
						if (body.user_email === "nonexistent@example.com") {
							return HttpResponse.json(
								{ detail: "Email address not found" },
								{ status: 404 },
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestVerificationEmail("nonexistent@example.com"),
			).rejects.toThrow("Email address not found");
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Invalid email format" }] },
						{ status: 422 },
					);
				}),
			);
			await expect(requestVerificationEmail("invalid-email")).rejects.toThrow(
				"Invalid email format",
			);
		});

		it("should handle service unavailable (503)", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const serviceUnavailableError = new Error("Service Unavailable");
			Object.defineProperty(serviceUnavailableError, "isAxiosError", {
				value: true,
			});
			Object.defineProperty(serviceUnavailableError, "response", {
				value: {
					status: 503,
					data: { detail: "Service down" },
				},
			});
			postSpy.mockRejectedValueOnce(serviceUnavailableError);

			await expect(
				requestVerificationEmail("test@example.com"),
			).rejects.toThrow(
				"Email service is temporarily unavailable. Please try again later.",
			);
			postSpy.mockRestore();
		});
	});

	describe("verifyEmail", () => {
		it("should verify email successfully when not from reset", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params, request }) => {
						const url = new URL(request.url);
						const fromReset = url.searchParams.get("fromReset") === "true";
						if (params.token === "valid-token") {
							return HttpResponse.json({
								message: fromReset
									? "Email verified successfully. You can now reset your password."
									: "Email verified successfully",
							});
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
			);
			const result = await verifyEmail("valid-token", false);
			expect(result).toEqual({ message: "Email verified successfully" });
		});

		it("should verify email successfully when from reset", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params, request }) => {
						const url = new URL(request.url);
						const fromReset = url.searchParams.get("fromReset") === "true";
						if (params.token === "valid-token-for-reset") {
							return HttpResponse.json({
								message: fromReset
									? "Email verified successfully. You can now reset your password."
									: "Email verified successfully",
							});
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
			);
			const result = await verifyEmail("valid-token-for-reset", true);
			expect(result).toEqual({
				message:
					"Email verified successfully. You can now reset your password.",
			});
		});

		it("should handle invalid verification token (400)", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params }) => {
						if (params.token === "invalid-token") {
							return HttpResponse.json(
								{ detail: "Invalid verification token" },
								{ status: 400 }, // Or 404 depending on API
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("invalid-token")).rejects.toThrow(
				"Invalid verification token",
			);
		});

		it("should handle invalid verification token (404)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications/:token"), () => {
					return HttpResponse.json(
						{ detail: "Token not found" },
						{ status: 404 },
					);
				}),
			);
			await expect(verifyEmail("not-found-token")).rejects.toThrow(
				AUTH_ERRORS.VERIFICATION_TOKEN_INVALID,
			);
		});

		it("should handle expired verification token", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					({ params }) => {
						if (params.token === "expired-token") {
							return HttpResponse.json(
								{ detail: "Token has expired" },
								{ status: 410 },
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("expired-token")).rejects.toThrow(
				AUTH_ERRORS.VERIFICATION_TOKEN_EXPIRED,
			);
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications/:token"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Validation issue" }] },
						{ status: 422 },
					);
				}),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("any-token")).rejects.toThrow(
				"Validation issue",
			);
		});
	});

	describe("requestPasswordReset", () => {
		it("should request password reset successfully if user exists and is verified", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), async ({ request }) => {
					const body = (await request.json()) as { user_email?: string };
					if (body.user_email === "verified@example.com") {
						return HttpResponse.json({ message: "Reset email sent" });
					}
					return HttpResponse.json(
						{ detail: "Unhandled mock" },
						{ status: 500 },
					);
				}),
			);
			await expect(
				requestPasswordReset("verified@example.com"),
			).resolves.toEqual({
				message: "Reset email sent",
			});
		});

		it("should handle email not found (404) as per current frontend logic", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: AUTH_ERRORS.EMAIL_NOT_FOUND },
						{ status: 404 },
					);
				}),
				http.options(buildUrl("/users/password-resets"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestPasswordReset("nonexistent@example.com"),
			).rejects.toThrow(AUTH_ERRORS.EMAIL_NOT_FOUND);
		});

		it("should handle email not verified (400) as per current frontend logic", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: "Email not verified" },
						{ status: 400 },
					);
				}),
				http.options(buildUrl("/users/password-resets"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestPasswordReset("unverified@example.com"),
			).rejects.toThrow("Email not verified");
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Invalid email for reset" }] },
						{ status: 422 },
					);
				}),
			);
			await expect(requestPasswordReset("bad-email@format")).rejects.toThrow(
				"Invalid email for reset",
			);
		});

		it("should handle service unavailable (503)", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const serviceUnavailableError = new Error("Service Unavailable");
			Object.defineProperty(serviceUnavailableError, "isAxiosError", {
				value: true,
			});
			Object.defineProperty(serviceUnavailableError, "response", {
				value: {
					status: 503,
					data: { detail: "Email service down" },
				},
			});
			postSpy.mockRejectedValueOnce(serviceUnavailableError);

			await expect(requestPasswordReset("any@example.com")).rejects.toThrow(
				"Email service is temporarily unavailable. Please try again later.",
			);
			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(requestPasswordReset("user@example.com")).rejects.toThrow(
				AUTH_ERRORS.NETWORK_ERROR,
			);
			postSpy.mockRestore();
		});
	});

	describe("resetPassword", () => {
		it("should reset password successfully", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params, request }) => {
						try {
							const body = (await request.json()) as {
								new_password?: string;
							};
							if (
								params.token === "valid-token" &&
								body.new_password === "NewPass123!"
							) {
								return HttpResponse.json({ message: "Password updated" });
							}
							return HttpResponse.json(
								{ detail: "Unhandled mock: wrong token or password" },
								{ status: 400 },
							);
						} catch (e) {
							return HttpResponse.json(
								{ detail: "MSW handler error" },
								{ status: 500 },
							);
						}
					},
				),
				http.options(buildUrl("/users/password-resets/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				resetPassword("valid-token", "NewPass123!"),
			).resolves.toEqual({
				message: "Password updated",
			});
		});

		it("should handle invalid or expired token (400)", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params }) => {
						if (params.token === "bad-token") {
							return HttpResponse.json(
								{ detail: "Invalid token" },
								{ status: 400 },
							);
						}
						return HttpResponse.json({ message: "Password updated" });
					},
				),
				http.options(buildUrl("/users/password-resets/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(resetPassword("bad-token", "NewPass123!")).rejects.toThrow(
				"Invalid token",
			);
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params, request }) => {
						const body = (await request.json()) as {
							new_password?: string;
						};
						if (
							params.token === "valid-token" &&
							body.new_password === "short"
						) {
							return HttpResponse.json(
								{
									detail: [{ loc: ["body", "new_password"], msg: "Too weak" }],
								},
								{ status: 422 },
							);
						}
						return HttpResponse.json({ message: "Password updated" });
					},
				),
				http.options(buildUrl("/users/password-resets/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(resetPassword("valid-token", "short")).rejects.toThrow(
				/Too weak/,
			);
		});

		it("should handle server errors (500)", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const err = new Error("Server down");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: { status: 500, data: {} },
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				AUTH_ERRORS.SERVER_ERROR,
			);
			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(apiModule.default, "post");
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				AUTH_ERRORS.NETWORK_ERROR,
			);
			postSpy.mockRestore();
		});
	});

	describe("checkEmailVerificationStatus", () => {
		it("should return true if email is verified", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					if (url.searchParams.get("user_email") === "verified@example.com") {
						return HttpResponse.json({ is_email_verified: true });
					}
					return HttpResponse.json({ detail: "Not found" }, { status: 404 });
				}),
			);

			const result = await checkEmailVerificationStatus("verified@example.com");
			expect(result).toEqual({ is_email_verified: true });
		});

		it("should return false if email is not verified", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					if (
						url.searchParams.get("user_email") === "notverified@example.com"
					) {
						return HttpResponse.json({ is_email_verified: false });
					}
					return HttpResponse.json({ detail: "Not found" }, { status: 404 });
				}),
			);

			const result = await checkEmailVerificationStatus(
				"notverified@example.com",
			);
			expect(result).toEqual({ is_email_verified: false });
		});

		it("should throw EMAIL_NOT_FOUND if user email is not found (404)", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), () => {
					return HttpResponse.json({ detail: "Not Found" }, { status: 404 });
				}),
			);

			await expect(
				checkEmailVerificationStatus("unknown@example.com"),
			).rejects.toThrow(AUTH_ERRORS.EMAIL_NOT_FOUND);
		});

		it("should throw FETCH_VERIFICATION_STATUS_FAILED for other server errors", async () => {
			await expect(
				checkEmailVerificationStatus("server-error@example.com"),
			).rejects.toThrow(AUTH_ERRORS.FETCH_VERIFICATION_STATUS_FAILED);
		}, 10000);

		it("should throw FETCH_VERIFICATION_STATUS_FAILED for network errors", async () => {
			const getSpy = vi.spyOn(apiModule.default, "get");
			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "request", { value: {} });
			getSpy.mockRejectedValueOnce(networkError);

			await expect(
				checkEmailVerificationStatus("test@example.com"),
			).rejects.toThrow(AUTH_ERRORS.FETCH_VERIFICATION_STATUS_FAILED);
			getSpy.mockRestore();
		});
	});
});
