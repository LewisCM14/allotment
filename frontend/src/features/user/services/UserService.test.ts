import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import * as errorMonitoring from "../../../services/errorMonitoring";
import {
	checkEmailVerificationStatus,
	requestVerificationEmail,
	getUserProfile,
	updateUserProfile,
	type UserProfileUpdate,
} from "./UserService";

// Mock error monitoring
vi.mock("../../../services/errorMonitoring", () => ({
	errorMonitor: {
		captureException: vi.fn(),
	},
}));

describe("UserService", () => {
	const mockErrorMonitor = {
		captureException: vi.fn(),
	};

	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		vi.clearAllMocks();

		// Reset error monitoring mock
		(errorMonitoring.errorMonitor as any) = mockErrorMonitor;
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

			// Should capture error for monitoring
			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "checkEmailVerificationStatus",
					url: "/users/verification-status",
					method: "GET",
					email: "any@example.com",
				}),
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

			// Should capture error for monitoring
			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "requestVerificationEmail",
					url: "/users/email-verifications",
					method: "POST",
					email: "test@example.com",
				}),
			);
		});
	});

	describe("getUserProfile", () => {
		it("should get user profile successfully", async () => {
			const mockProfile = {
				user_id: "123",
				user_email: "test@example.com",
				user_first_name: "Test",
				user_country_code: "GB",
				is_email_verified: true,
			};

			server.use(
				http.get(buildUrl("/users/profile"), () => {
					return HttpResponse.json(mockProfile);
				}),
			);

			const result = await getUserProfile();

			expect(result).toEqual(mockProfile);
		});

		it("should handle unauthorized errors", async () => {
			server.use(
				http.get(buildUrl("/users/profile"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: "Unauthorized",
						}),
						{
							status: 401,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(getUserProfile()).rejects.toThrow();

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "getUserProfile",
					url: "/users/profile",
					method: "GET",
				}),
			);
		});

		it("should handle network errors", async () => {
			vi.spyOn(api, "get").mockRejectedValueOnce(new Error("Network Error"));

			await expect(getUserProfile()).rejects.toThrow(
				"Failed to fetch user profile. Please try again.",
			);

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "getUserProfile",
					url: "/users/profile",
					method: "GET",
				}),
			);
		});
	});

	describe("updateUserProfile", () => {
		const validProfileData: UserProfileUpdate = {
			user_first_name: "Updated Name",
			user_country_code: "US",
		};

		it("should update user profile successfully", async () => {
			const mockUpdatedProfile = {
				user_id: "123",
				user_email: "test@example.com",
				user_first_name: "Updated Name",
				user_country_code: "US",
				is_email_verified: true,
			};

			server.use(
				http.put(buildUrl("/users/profile"), async ({ request }) => {
					const body = await request.json();
					expect(body).toEqual(validProfileData);
					return HttpResponse.json(mockUpdatedProfile);
				}),
			);

			const result = await updateUserProfile(validProfileData);

			expect(result).toEqual(mockUpdatedProfile);
		});

		it("should handle validation errors", async () => {
			server.use(
				http.put(buildUrl("/users/profile"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: [
								{
									msg: "String should have at least 2 characters",
									type: "string_too_short",
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

			await expect(updateUserProfile(validProfileData)).rejects.toThrow();

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "updateUserProfile",
					url: "/users/profile",
					method: "PUT",
					data: validProfileData,
				}),
			);
		});

		it("should handle server errors", async () => {
			server.use(
				http.put(buildUrl("/users/profile"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: "Internal server error",
						}),
						{
							status: 500,
							headers: {
								"content-type": "application/json",
							},
						},
					);
				}),
			);

			await expect(updateUserProfile(validProfileData)).rejects.toThrow();

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "updateUserProfile",
					url: "/users/profile",
					method: "PUT",
					data: validProfileData,
				}),
			);
		});

		it("should handle network errors", async () => {
			vi.spyOn(api, "put").mockRejectedValueOnce(new Error("Network Error"));

			await expect(updateUserProfile(validProfileData)).rejects.toThrow(
				"Failed to update user profile. Please try again.",
			);

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "updateUserProfile",
					url: "/users/profile",
					method: "PUT",
					data: validProfileData,
				}),
			);
		});

		it("should handle empty profile data", async () => {
			const emptyData: UserProfileUpdate = {
				user_first_name: "",
				user_country_code: "",
			};

			server.use(
				http.put(buildUrl("/users/profile"), () => {
					return new HttpResponse(
						JSON.stringify({
							detail: "Validation failed",
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

			await expect(updateUserProfile(emptyData)).rejects.toThrow();

			expect(mockErrorMonitor.captureException).toHaveBeenCalledWith(
				expect.any(Error),
				expect.objectContaining({
					context: "updateUserProfile",
					data: emptyData,
				}),
			);
		});
	});
});
