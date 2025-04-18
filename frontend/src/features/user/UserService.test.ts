import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as apiModule from "../../services/api";
import {
	AUTH_ERRORS,
	loginUser,
	registerUser,
	requestPasswordReset,
	requestVerificationEmail,
	resetPassword,
	verifyEmail,
} from "./UserService";

const mockFetch = (response: unknown, status = 200) => {
	global.fetch = vi.fn(() =>
		Promise.resolve(
			new Response(JSON.stringify(response), {
				status,
				headers: { "Content-Type": "application/json" },
			}),
		),
	);
};

describe("UserService", () => {
	beforeEach(() => {
		// Ensure navigator.onLine is true for all tests
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});

		// Clear localStorage before each test
		localStorage.clear();
	});

	describe("loginUser", () => {
		it("should log in a user with valid credentials", async () => {
			const mockResponse = {
				access_token: "mock-access-token",
				refresh_token: "mock-refresh-token",
				user_first_name: "Test",
				is_email_verified: false,
				user_id: "",
			};
			mockFetch(mockResponse);

			const result = await loginUser("test@example.com", "password123");

			expect(result).toEqual({
				tokens: {
					access_token: "mock-access-token",
					refresh_token: "mock-refresh-token",
				},
				firstName: "Test",
				userData: {
					user_email: "test@example.com",
					user_id: "",
					is_email_verified: false,
				},
			});
		});

		it("should throw an error with invalid credentials", async () => {
			mockFetch({ detail: "Invalid email or password" }, 401);

			await expect(loginUser("wrong@example.com", "wrong")).rejects.toThrow(
				AUTH_ERRORS.INVALID_CREDENTIALS,
			);
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
			const mockResponse = {
				access_token: "new-access-token",
				refresh_token: "new-refresh-token",
			};
			mockFetch(mockResponse);

			const result = await registerUser(
				"new@example.com",
				"password123",
				"John",
				"US",
			);

			expect(result).toEqual(mockResponse);
		});

		it("should throw an error if email already exists", async () => {
			mockFetch({ detail: "Email already registered" }, 409);

			await expect(
				registerUser("exists@example.com", "password123", "John", "US"),
			).rejects.toThrow(AUTH_ERRORS.EMAIL_EXISTS);
		});

		it("should handle validation errors from the server", async () => {
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
			const result = await requestVerificationEmail("test@example.com");
			expect(result).toEqual({ message: "Verification email sent" });
		});

		it("should handle email not found error", async () => {
			await expect(
				requestVerificationEmail("nonexistent@example.com"),
			).rejects.toThrow("Email address not found");
		});
	});

	describe("verifyEmail", () => {
		it("should verify email successfully", async () => {
			const result = await verifyEmail("valid-token");
			expect(result).toEqual({ message: "Email verified successfully" });
		});

		it("should handle invalid verification token", async () => {
			await expect(verifyEmail("invalid-token")).rejects.toThrow(
				"Invalid verification token",
			);
		});

		it("should handle expired verification token", async () => {
			await expect(verifyEmail("expired-token")).rejects.toThrow(
				AUTH_ERRORS.VERIFICATION_TOKEN_EXPIRED,
			);
		});
	});

	describe("requestPasswordReset", () => {
		// biome-ignore lint/suspicious/noExplicitAny: any is fine in this context
		let postSpy: any;

		beforeEach(() => {
			postSpy = vi.spyOn(apiModule.default, "post");
		});
		afterEach(() => {
			postSpy.mockRestore();
		});

		it("should request password reset successfully", async () => {
			postSpy.mockResolvedValueOnce({ data: { message: "Reset email sent" } });
			await expect(requestPasswordReset("user@example.com")).resolves.toEqual({
				message: "Reset email sent",
			});
		});

		it("should handle email not found error (404)", async () => {
			const err = new Error("Not found");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: { status: 404, data: {} },
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(requestPasswordReset("user@example.com")).rejects.toThrow(
				AUTH_ERRORS.EMAIL_NOT_FOUND,
			);
		});

		it("should handle network errors", async () => {
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(requestPasswordReset("user@example.com")).rejects.toThrow(
				AUTH_ERRORS.NETWORK_ERROR,
			);
		});
	});

	describe("resetPassword", () => {
		// biome-ignore lint/suspicious/noExplicitAny: any is fine in this context
		let postSpy: any;

		beforeEach(() => {
			postSpy = vi.spyOn(apiModule.default, "post");
		});
		afterEach(() => {
			postSpy.mockRestore();
		});

		it("should reset password successfully", async () => {
			postSpy.mockResolvedValueOnce({ data: { message: "Password updated" } });
			await expect(
				resetPassword("valid-token", "NewPass123!"),
			).resolves.toEqual({
				message: "Password updated",
			});
		});

		it("should handle invalid or expired token (400)", async () => {
			const err = new Error("Bad request");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: { status: 400, data: { detail: "Invalid token" } },
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("bad-token", "NewPass123!")).rejects.toThrow(
				"Invalid token",
			);
		});

		it("should handle validation errors (422)", async () => {
			const err = new Error("Unprocessable");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: {
					status: 422,
					data: {
						detail: [{ loc: ["body", "new_password"], msg: "Too weak" }],
					},
				},
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("valid-token", "short")).rejects.toThrow(
				/Too weak/,
			);
		});

		it("should handle server errors (500)", async () => {
			const err = new Error("Server down");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: { status: 500, data: {} },
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				AUTH_ERRORS.SERVER_ERROR,
			);
		});

		it("should handle network errors", async () => {
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				AUTH_ERRORS.NETWORK_ERROR,
			);
		});
	});
});
