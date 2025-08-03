import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import {
	checkEmailVerificationStatus,
	requestVerificationEmail,
} from "./UserService";

describe("UserService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		vi.clearAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("checkEmailVerificationStatus", () => {
		it("should check verification status successfully", async () => {
			const mockResponse = { is_email_verified: true };

			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					const userEmail = url.searchParams.get("user_email");
					expect(userEmail).toBe("test@example.com");
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await checkEmailVerificationStatus("test@example.com");

			expect(result).toEqual(mockResponse);
		});

		it("should return unverified status", async () => {
			const mockResponse = { is_email_verified: false };

			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					const userEmail = url.searchParams.get("user_email");
					expect(userEmail).toBe("unverified@example.com");
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await checkEmailVerificationStatus(
				"unverified@example.com",
			);

			expect(result).toEqual(mockResponse);
		});

		it("should handle user not found errors", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: "User not found",
						}),
						{
							status: 404,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(
				checkEmailVerificationStatus("notfound@example.com"),
			).rejects.toThrow("User not found");
		});

		it("should handle network errors appropriately", async () => {
			vi.spyOn(api, "get").mockRejectedValueOnce(new Error("Network Error"));

			await expect(
				checkEmailVerificationStatus("any@example.com"),
			).rejects.toThrow(
				"Failed to fetch verification status. Please try again.",
			);
		});
	});

	describe("requestVerificationEmail", () => {
		it("should request verification email successfully", async () => {
			const mockResponse = {
				message: "Verification email sent successfully",
			};

			server.use(
				http.post(
					buildUrl("/users/email-verifications"),
					async ({ request }) => {
						const body = await request.json();
						expect(body).toEqual({ user_email: "test@example.com" });
						return HttpResponse.json(mockResponse);
					},
				),
			);

			const result = await requestVerificationEmail("test@example.com");

			expect(result).toEqual(mockResponse);
		});

		it("should handle validation errors", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications"), () => {
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

			await expect(requestVerificationEmail("invalid-email")).rejects.toThrow(
				"Invalid email format",
			);
		});

		it("should handle network errors appropriately", async () => {
			vi.spyOn(api, "post").mockRejectedValueOnce(new Error("Network Error"));

			await expect(
				requestVerificationEmail("test@example.com"),
			).rejects.toThrow("Failed to send verification email");
		});
	});
});
