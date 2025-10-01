import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import {
	loginUser,
	refreshAccessToken,
	requestPasswordReset,
	resetPassword,
} from "./AuthService";
describe("AuthService", () => {
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
				"Invalid email or password. Please try again.",
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
			).rejects.toThrow("User not found");
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
				"Account locked",
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
			const postSpy = vi.spyOn(api, "post");

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
			).rejects.toThrow("Server error. Please try again later.");

			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(api, "post");

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

	describe("refreshAccessToken", () => {
		beforeEach(() => {
			localStorage.setItem("refresh_token", "existing-refresh-token");
		});

		it("should refresh tokens successfully", async () => {
			server.use(
				http.post(buildUrl("/auth/token/refresh"), () => {
					return HttpResponse.json({
						access_token: "new-access-token",
						refresh_token: "new-refresh-token",
						token_type: "bearer",
						user_first_name: "Test",
						user_id: "user-123",
						is_email_verified: true,
					});
				}),
			);

			const result = await refreshAccessToken();

			expect(result).toEqual({
				access_token: "new-access-token",
				refresh_token: "new-refresh-token",
				token_type: "bearer",
				user_first_name: "Test",
				user_id: "user-123",
				is_email_verified: true,
			});
			expect(localStorage.getItem("access_token")).toBe("new-access-token");
			expect(localStorage.getItem("refresh_token")).toBe("new-refresh-token");
		});

		it("should handle invalid refresh token", async () => {
			server.use(
				http.post(buildUrl("/auth/token/refresh"), () => {
					return HttpResponse.json(
						{ detail: "Invalid token" },
						{ status: 401 },
					);
				}),
			);

			await expect(refreshAccessToken()).rejects.toThrow(
				"Invalid email or password. Please try again.",
			);
			expect(localStorage.getItem("access_token")).toBeNull();
			expect(localStorage.getItem("refresh_token")).toBeNull();
		});

		it("should handle missing refresh token", async () => {
			localStorage.removeItem("refresh_token");

			await expect(refreshAccessToken()).rejects.toThrow(
				"Failed to refresh authentication token",
			);
		});

		it("should handle network errors during token refresh", async () => {
			const postSpy = vi.spyOn(api, "post");

			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "response", { value: undefined });
			Object.defineProperty(networkError, "request", { value: {} });

			postSpy.mockRejectedValueOnce(networkError);

			await expect(refreshAccessToken()).rejects.toThrow(/Network error/i);
			expect(localStorage.getItem("access_token")).toBeNull();
			expect(localStorage.getItem("refresh_token")).toBeNull();

			postSpy.mockRestore();
		});

		it("should handle server errors during token refresh", async () => {
			server.use(
				http.post(buildUrl("/auth/token/refresh"), () => {
					return HttpResponse.json({ detail: "Server error" }, { status: 500 });
				}),
			);

			await expect(refreshAccessToken()).rejects.toThrow("Server error");
			expect(localStorage.getItem("access_token")).toBeNull();
			expect(localStorage.getItem("refresh_token")).toBeNull();
		});
	});

	describe("requestPasswordReset", () => {
		it("should request password reset successfully", async () => {
			const mockResponse = {
				message:
					"If your email exists in our system and is verified, you will receive a password reset link shortly.",
			};

			server.use(
				http.post(buildUrl("/auth/password-resets"), async ({ request }) => {
					const body = await request.json();
					expect(body).toEqual({ user_email: "test@example.com" });
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await requestPasswordReset("test@example.com");

			expect(result).toEqual(mockResponse);
		});

		it("should handle user not found gracefully", async () => {
			const mockResponse = {
				message:
					"If your email exists in our system and is verified, you will receive a password reset link shortly.",
			};

			server.use(
				http.post(buildUrl("/auth/password-resets"), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			// Even for non-existent users, the service should return the same message for security
			const result = await requestPasswordReset("nonexistent@example.com");

			expect(result).toEqual(mockResponse);
		});

		it("should handle validation errors", async () => {
			server.use(
				http.post(buildUrl("/auth/password-resets"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: [
								{
									msg: "Invalid email format",
									type: "value_error.email",
								},
							],
						}),
						{
							status: 422,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(requestPasswordReset("invalid-email")).rejects.toThrow(
				"Invalid email format",
			);
		});

		it("should handle network errors appropriately", async () => {
			vi.spyOn(api, "post").mockRejectedValueOnce(new Error("Network Error"));

			await expect(requestPasswordReset("test@example.com")).rejects.toThrow(
				"Password reset failed. Please try again later.",
			);
		});
	});

	describe("resetPassword", () => {
		it("should reset password successfully", async () => {
			const mockResponse = { message: "Password has been reset successfully" };

			server.use(
				http.post(
					buildUrl("/auth/password-resets/valid-reset-token"),
					async ({ request }) => {
						const body = await request.json();
						expect(body).toEqual({ new_password: "newPassword123!" });
						return HttpResponse.json(mockResponse);
					},
				),
			);
			const result = await resetPassword(
				"valid-reset-token",
				"newPassword123!",
			);

			expect(result).toEqual(mockResponse);
		});

		it("should handle invalid token errors", async () => {
			server.use(
				http.post(buildUrl("/auth/password-resets/invalid-token"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: [
								{
									msg: "Invalid or expired reset token",
									type: "invalid_token_error",
								},
							],
						}),
						{
							status: 400,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(
				resetPassword("invalid-token", "newPassword123!"),
			).rejects.toThrow("Invalid or expired reset token");
		});

		it("should handle token expiry errors", async () => {
			server.use(
				http.post(buildUrl("/auth/password-resets/expired-token"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: [
								{
									msg: "Reset token has expired",
									type: "token_expired_error",
								},
							],
						}),
						{
							status: 400,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(
				resetPassword("expired-token", "newPassword123!"),
			).rejects.toThrow("Reset token has expired");
		});

		it("should handle password validation errors", async () => {
			server.use(
				http.post(buildUrl("/auth/password-resets/valid-token"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: [
								{
									msg: "Password must be at least 8 characters long",
									type: "value_error.password_too_short",
								},
							],
						}),
						{
							status: 422,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(resetPassword("valid-token", "weak")).rejects.toThrow(
				"Password must be at least 8 characters long",
			);
		});

		it("should handle network errors appropriately", async () => {
			vi.spyOn(api, "post").mockRejectedValueOnce(new Error("Network Error"));

			await expect(
				resetPassword("any-token", "newPassword123!"),
			).rejects.toThrow("Failed to reset password");
		});
	});
});
