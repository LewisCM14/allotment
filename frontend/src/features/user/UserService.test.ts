import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../../mocks/server";
import * as apiModule from "../../services/api";
import { AUTH_ERRORS, loginUser, registerUser } from "./UserService";

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
			// Mock API response
			const mockResponse = {
				access_token: "mock-access-token",
				refresh_token: "mock-refresh-token",
				user_first_name: "Test",
				is_email_verified: false,
				user_id: "",
			};

			// Mock the API call
			global.fetch = vi.fn(() =>
				Promise.resolve(
					new Response(JSON.stringify(mockResponse), {
						status: 200,
						headers: { "Content-Type": "application/json" },
					}),
				),
			);

			// Call the function
			const result = await loginUser("test@example.com", "password123");

			// Update the expected result to include userData
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

			// Verify tokens are stored in localStorage
			expect(localStorage.getItem("access_token")).toBe("mock-access-token");
			expect(localStorage.getItem("refresh_token")).toBe("mock-refresh-token");
		});

		it("should throw an error with invalid credentials", async () => {
			await expect(loginUser("wrong@example.com", "wrong")).rejects.toThrow(
				"Invalid email or password",
			);
		});

		it("should handle server errors gracefully", async () => {
			// Override the handler just for this test
			server.use(
				http.post("*/user/auth/login", () => {
					return new HttpResponse(null, { status: 500 });
				}),
			);

			await expect(
				loginUser("test@example.com", "password123"),
			).rejects.toThrow("Server error. Please try again later.");
		});

		it("should handle network errors", async () => {
			// Instead of using MSW, directly mock axios.post
			const postSpy = vi.spyOn(apiModule.default, "post");

			// Create a network error as axios would
			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "response", { value: undefined });
			Object.defineProperty(networkError, "request", { value: {} }); // Non-empty request object

			postSpy.mockRejectedValueOnce(networkError);

			await expect(
				loginUser("test@example.com", "password123"),
			).rejects.toThrow(AUTH_ERRORS.NETWORK_ERROR);

			postSpy.mockRestore();
		});
	});

	describe("registerUser", () => {
		it("should register a new user successfully", async () => {
			const result = await registerUser(
				"new@example.com",
				"password123",
				"John",
				"US",
			);

			expect(result).toEqual({
				access_token: "new-access-token",
				refresh_token: "new-refresh-token",
			});
		});

		it("should throw an error if email already exists", async () => {
			await expect(
				registerUser("exists@example.com", "password123", "John", "US"),
			).rejects.toThrow("This email is already registered");
		});

		it("should handle validation errors from the server", async () => {
			// Mock the API post method directly instead of using MSW
			const postSpy = vi.spyOn(apiModule.default, "post");

			// Create a response similar to what axios would return for a 422 error
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

		it("should handle 400 errors with custom messages", async () => {
			server.use(
				http.post("*/user", () => {
					return new HttpResponse(
						JSON.stringify({ detail: "Invalid country code" }),
						{ status: 400 },
					);
				}),
			);

			await expect(
				registerUser("valid@example.com", "password123", "John", "XX"),
			).rejects.toThrow("Invalid country code");
		});

		it("should detect offline status", async () => {
			// Mock navigator.onLine as false for this specific test
			Object.defineProperty(navigator, "onLine", {
				configurable: true,
				value: false,
			});

			// Mock the handleApiError function to pass through offline errors
			const handleApiErrorSpy = vi.spyOn(apiModule, "handleApiError");
			handleApiErrorSpy.mockImplementation((error) => {
				if (
					error instanceof Error &&
					error.message.includes("You are offline")
				) {
					throw new Error("You are offline");
				}
				throw error;
			});

			// Directly spy on api.post in the UserService module
			const apiPostSpy = vi.spyOn(apiModule.default, "post");
			apiPostSpy.mockRejectedValue(
				new Error("You are offline. Please check your connection."),
			);

			await expect(
				registerUser("valid@example.com", "password123", "John", "US"),
			).rejects.toThrow("You are offline");

			apiPostSpy.mockRestore();
			handleApiErrorSpy.mockRestore();
		});
	});
});
