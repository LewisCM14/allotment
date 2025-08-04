import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import { registerUser, verifyEmail } from "./RegistrationService";

describe("RegistrationService", () => {
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
				http.post(buildUrl("/registration"), () => {
					return HttpResponse.json(mockApiResponse);
				}),
				http.options(buildUrl("/registration"), () => {
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
				http.post(buildUrl("/registration"), () => {
					return HttpResponse.json(
						{ detail: "Email already registered" },
						{ status: 409 },
					);
				}),
				http.options(buildUrl("/registration"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				registerUser("exists@example.com", "password123", "John", "US"),
			).rejects.toThrow("Email already registered");
		});

		it("should handle bad request errors (400)", async () => {
			server.use(
				http.post(buildUrl("/registration"), () => {
					return HttpResponse.json(
						{ detail: "Bad request data" },
						{ status: 400 },
					);
				}),
				http.options(buildUrl("/registration"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				registerUser("bad@example.com", "password", "Bad", "XX"),
			).rejects.toThrow("Bad request data");
		});

		it("should handle validation errors from the server (422)", async () => {
			const postSpy = vi.spyOn(api, "post");
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

	describe("verifyEmail", () => {
		it("should verify email successfully with token", async () => {
			const mockResponse = { message: "Email verified successfully" };

			server.use(
				http.post(
					buildUrl("/registration/email-verifications/valid-token"),
					({ request }) => {
						const url = new URL(request.url);
						expect(url.searchParams.get("fromReset")).toBe("false");
						return HttpResponse.json(mockResponse);
					},
				),
			);

			const result = await verifyEmail("valid-token");

			expect(result).toEqual(mockResponse);
		});

		it("should verify email with fromReset parameter", async () => {
			const mockResponse = { message: "Email verified for password reset" };

			server.use(
				http.post(
					buildUrl("/registration/email-verifications/reset-token"),
					({ request }) => {
						const url = new URL(request.url);
						expect(url.searchParams.get("fromReset")).toBe("true");
						return HttpResponse.json(mockResponse);
					},
				),
			);

			const result = await verifyEmail("reset-token", true);

			expect(result).toEqual(mockResponse);
		});

		it("should handle invalid token errors", async () => {
			server.use(
				http.post(
					buildUrl("/registration/email-verifications/invalid-token"),
					() => {
						return new HttpResponse(
							JSON.stringify({
								detail: [
									{
										msg: "Invalid or expired verification token",
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
					},
				),
			);

			await expect(verifyEmail("invalid-token")).rejects.toThrow(
				"Invalid or expired verification token",
			);
		});

		it("should handle network errors appropriately", async () => {
			vi.spyOn(api, "post").mockRejectedValueOnce(new Error("Network Error"));

			await expect(verifyEmail("any-token")).rejects.toThrow(
				"Email verification failed. Please request a new verification link.",
			);
		});
	});
});
