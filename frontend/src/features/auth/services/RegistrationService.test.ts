import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import { registerUser } from "./RegistrationService";

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
			).rejects.toThrow("Email already registered");
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
});
