import { http, HttpResponse } from "msw";
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	it,
	vi,
	type Mock,
	type MockInstance,
} from "vitest";
import axios from "axios";
import { server } from "../mocks/server";
import api, { handleApiError } from "./api";
import { errorMonitor } from "./errorMonitoring";
import { API_URL, API_VERSION } from "./apiConfig";

describe("API Service", () => {
	beforeEach(() => {
		localStorage.clear();
		vi.spyOn(console, "error").mockImplementation(() => { });
	});

	afterEach(() => {
		vi.restoreAllMocks();
		server.resetHandlers();
	});

	describe("Error handling", () => {
		it("should format API errors based on status code", () => {
			const mockError = {
				isAxiosError: true,
				response: {
					status: 401,
					data: { detail: "Invalid credentials" },
				},
			};

			vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

			expect(() => handleApiError(mockError, "Default error message")).toThrow(
				"Invalid email or password. Please try again.",
			);
		});

		it("should handle validation errors (422)", () => {
			const mockError = {
				isAxiosError: true,
				response: {
					status: 422,
					data: {
						detail: [
							{ msg: "Field is required", loc: ["field"] },
							{ msg: "Invalid format", loc: ["email"] },
						],
					},
				},
			};

			vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

			expect(() => handleApiError(mockError, "Default error message")).toThrow(
				JSON.stringify([
					{ msg: "Field is required", loc: ["field"] },
					{ msg: "Invalid format", loc: ["email"] },
				]),
			);
		});

		it("should handle network errors", () => {
			const mockError = {
				isAxiosError: true,
				response: undefined,
			};

			vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

			expect(() => handleApiError(mockError, "Default error message")).toThrow(
				"Network error. Please check your connection and try again.",
			);
		});

		it("should handle 500 server errors", () => {
			const mockError = {
				isAxiosError: true,
				response: {
					status: 500,
					data: { detail: "Internal server error" },
				},
			};

			vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

			expect(() => handleApiError(mockError, "Default error message")).toThrow(
				"Server error. Please try again later.",
			);
		});
	});

	describe("Token refresh", () => {
		beforeEach(() => {
			localStorage.setItem("refresh_token", "test-refresh-token");
		});

		it("should refresh token on 401 and retry original request", async () => {
			let authAttempts = 0;
			let refreshAttempts = 0;

			server.use(
				http.get("*/test-endpoint", ({ request }) => {
					authAttempts++;
					const authHeader = request.headers.get("authorization");

					if (!authHeader || authHeader === "Bearer invalid-token") {
						return HttpResponse.json(
							{ detail: "Token expired" },
							{ status: 401 },
						);
					}

					return HttpResponse.json({ data: "success" });
				}),
				http.post("*/auth/token/refresh", () => {
					refreshAttempts++;
					return HttpResponse.json({
						access_token: "new-access-token",
						refresh_token: "new-refresh-token",
					});
				}),
			);

			localStorage.setItem("access_token", "invalid-token");

			const response = await api.get("/test-endpoint");

			expect(authAttempts).toBe(2); // First attempt + retry after refresh
			expect(refreshAttempts).toBe(1);
			expect(response.data).toEqual({ data: "success" });
			expect(localStorage.getItem("access_token")).toBe("new-access-token");
		});

		it("should handle refresh token failure", async () => {
			server.use(
				http.get("*/test-endpoint", () => {
					return HttpResponse.json(
						{ detail: "Token expired" },
						{ status: 401 },
					);
				}),
				http.post("*/auth/token/refresh", () => {
					return HttpResponse.json(
						{ detail: "Refresh token expired" },
						{ status: 401 },
					);
				}),
			);

			// Mock window.location.href
			const originalLocation = window.location;
			Object.defineProperty(window, "location", {
				value: { href: "" },
				writable: true,
			});

			localStorage.setItem("access_token", "invalid-token");

			await expect(api.get("/test-endpoint")).rejects.toThrow();

			// Tokens should be cleared
			expect(localStorage.getItem("access_token")).toBeNull();
			expect(localStorage.getItem("refresh_token")).toBeNull();
		});

		it("should queue multiple requests during token refresh", async () => {
			let refreshAttempts = 0;

			server.use(
				http.get("*/test-endpoint-1", ({ request }) => {
					const authHeader = request.headers.get("authorization");
					if (!authHeader || authHeader === "Bearer invalid-token") {
						return HttpResponse.json(
							{ detail: "Token expired" },
							{ status: 401 },
						);
					}
					return HttpResponse.json({ data: "endpoint-1" });
				}),
				http.get("*/test-endpoint-2", ({ request }) => {
					const authHeader = request.headers.get("authorization");
					if (!authHeader || authHeader === "Bearer invalid-token") {
						return HttpResponse.json(
							{ detail: "Token expired" },
							{ status: 401 },
						);
					}
					return HttpResponse.json({ data: "endpoint-2" });
				}),
				http.post("*/auth/token/refresh", async () => {
					refreshAttempts++;
					// Simulate network delay
					await new Promise((resolve) => setTimeout(resolve, 100));
					return HttpResponse.json({
						access_token: "new-access-token",
						refresh_token: "new-refresh-token",
					});
				}),
			);

			localStorage.setItem("access_token", "invalid-token");

			// Make multiple concurrent requests
			const [response1, response2] = await Promise.all([
				api.get("/test-endpoint-1"),
				api.get("/test-endpoint-2"),
			]);

			// Only one refresh should occur
			expect(refreshAttempts).toBe(1);
			expect(response1.data).toEqual({ data: "endpoint-1" });
			expect(response2.data).toEqual({ data: "endpoint-2" });
		});
	});

	describe("Request retry logic", () => {
		it("should retry on network errors", async () => {
			let attempts = 0;

			server.use(
				http.get("*/retry-test", () => {
					attempts++;
					if (attempts < 3) {
						return HttpResponse.error();
					}
					return HttpResponse.json({ success: true });
				}),
			);

			const response = await api.get("/retry-test");
			expect(attempts).toBe(3);
			expect(response.data).toEqual({ success: true });
		});

		it("should retry on 5xx server errors", async () => {
			let attempts = 0;

			server.use(
				http.get("*/server-error-test", () => {
					attempts++;
					if (attempts < 2) {
						return HttpResponse.json(
							{ error: "Server error" },
							{ status: 500 },
						);
					}
					return HttpResponse.json({ success: true });
				}),
			);

			const response = await api.get("/server-error-test");
			expect(attempts).toBe(2);
			expect(response.data).toEqual({ success: true });
		});

		it("should not retry on 4xx client errors (except 401)", async () => {
			let attempts = 0;

			server.use(
				http.get("*/client-error-test", () => {
					attempts++;
					return HttpResponse.json({ error: "Bad request" }, { status: 400 });
				}),
			);

			await expect(api.get("/client-error-test")).rejects.toThrow();
			expect(attempts).toBe(1);
		});

		it("should eventually fail after max retries", async () => {
			let attempts = 0;

			server.use(
				http.get("*/always-fail", () => {
					attempts++;
					return HttpResponse.error();
				}),
			);

			await expect(api.get("/always-fail")).rejects.toThrow();
			expect(attempts).toBe(4); // Initial + 3 retries
		});
	});

	describe("URL normalization", () => {
		it("should normalize relative URLs with API version", async () => {
			server.use(
				http.get(`${API_URL}${API_VERSION}/test-endpoint`, () => {
					return HttpResponse.json({ success: true });
				}),
			);

			const response = await api.get("/test-endpoint");
			expect(response.data).toEqual({ success: true });
		});

		it("should handle absolute URLs without modification", async () => {
			server.use(
				http.get("https://external-api.com/data", ({ request }) => {
					return HttpResponse.json({ external: true });
				}),
			);

			const response = await api.get("https://external-api.com/data");
			expect(response.data).toEqual({ external: true });
		});
	});

	describe("Request cancellation", () => {
		it("should cancel duplicate search requests", async () => {
			let completedRequests = 0;

			server.use(
				http.get("*/search", async () => {
					await new Promise((resolve) => setTimeout(resolve, 100));
					completedRequests++;
					return HttpResponse.json({ results: [] });
				}),
			);

			// Start multiple search requests rapidly
			const requests = [
				api.get("/search", { params: { q: "test" } }),
				api.get("/search", { params: { q: "test" } }),
				api.get("/search", { params: { q: "test" } }),
			];

			// Only the last request should complete successfully
			// Previous ones should be cancelled
			const results = await Promise.allSettled(requests);

			// Some requests should be cancelled/rejected, only one should succeed
			const successful = results.filter((r) => r.status === "fulfilled");
			expect(successful.length).toBeLessThanOrEqual(1);
		});
	});
});
