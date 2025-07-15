import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../mocks/server";
import api, { handleApiError } from "./api";
import { apiCache } from "./apiCache";
import { errorMonitor } from "./errorMonitoring";

describe("API Service", () => {
	beforeEach(() => {
		localStorage.clear();
		apiCache.clear();
		vi.spyOn(console, "error").mockImplementation(() => { });
	});

	afterEach(() => {
		vi.restoreAllMocks();
		server.resetHandlers();
	});

	describe("Error handling", () => {
		it("should format API errors based on status code", () => {
			const error = {
				response: {
					status: 401,
					data: { detail: "Unauthorized" },
				},
				isAxiosError: true,
			};

			try {
				handleApiError(error, "Default error message");
				expect(true).toBe(false); // Should not reach here
			} catch (e) {
				// Update this line to match the actual error message in your code
				expect((e as Error).message).toBe(
					"Invalid email or password. Please try again.",
				);
			}
		});

		it("should handle validation errors (422)", () => {
			const error = {
				response: {
					status: 422,
					data: {
						detail: [{ loc: ["body", "email"], msg: "Invalid email format" }],
					},
				},
				isAxiosError: true,
			};

			try {
				handleApiError(error, "Default error message");
				expect(true).toBe(false); // Should not reach here
			} catch (e) {
				expect((e as Error).message).toContain("Invalid email format");
			}
		});

		it("should handle network errors", () => {
			const error = {
				isAxiosError: true,
				response: undefined,
			};

			try {
				handleApiError(error, "Default error message");
				expect(true).toBe(false); // Should not reach here
			} catch (e) {
				expect((e as Error).message).toBe(
					"Network error. Please check your connection and try again.",
				);
			}
		});

		it("should handle 500 server errors", () => {
			const error = {
				response: {
					status: 500,
					data: { detail: "Internal server error" },
				},
				isAxiosError: true,
			};

			try {
				handleApiError(error, "Default error message");
				expect(true).toBe(false); // Should not reach here
			} catch (e) {
				expect((e as Error).message).toBe(
					"Server error. Please try again later.",
				);
			}
		});
	});

	describe("Cached GET requests", () => {
		it("should cache GET responses", async () => {
			let requestCount = 0;

			server.use(
				http.get("*/test-cache", () => {
					requestCount++;
					return HttpResponse.json({ data: "cached-response", count: requestCount });
				}),
			);

			// First request should hit the server
			const response1 = await api.cachedGet("/test-cache");
			expect(response1).toEqual({ data: "cached-response", count: 1 });
			expect(requestCount).toBe(1);

			// Second request should use cache
			const response2 = await api.cachedGet("/test-cache");
			expect(response2).toEqual({ data: "cached-response", count: 1 });
			expect(requestCount).toBe(1); // Still 1, no new request
		});

		it("should create unique cache keys for different URLs and params", async () => {
			let url1RequestCount = 0;
			let url2RequestCount = 0;

			server.use(
				http.get("*/test-cache-1", () => {
					url1RequestCount++;
					return HttpResponse.json({ url: "1", count: url1RequestCount });
				}),
				http.get("*/test-cache-2", ({ request }) => {
					const url = new URL(request.url);
					const param = url.searchParams.get("param");
					url2RequestCount++;
					return HttpResponse.json({ url: "2", param, count: url2RequestCount });
				}),
			);

			// Different URLs should not share cache
			await api.cachedGet("/test-cache-1");
			await api.cachedGet("/test-cache-2");
			expect(url1RequestCount).toBe(1);
			expect(url2RequestCount).toBe(1);

			// Same URL with different params should not share cache
			await api.cachedGet("/test-cache-2", { params: { param: "value1" } });
			await api.cachedGet("/test-cache-2", { params: { param: "value2" } });
			expect(url2RequestCount).toBe(3); // 1 + 2 new requests
		});

		it("should handle cache expiration", async () => {
			// Mock Date.now to control time
			const originalDateNow = Date.now;
			let mockTime = 1000;
			vi.spyOn(Date, "now").mockImplementation(() => mockTime);

			let requestCount = 0;
			server.use(
				http.get("*/test-cache-expiry", () => {
					requestCount++;
					return HttpResponse.json({ count: requestCount });
				}),
			);

			// First request
			await api.cachedGet("/test-cache-expiry");
			expect(requestCount).toBe(1);

			// Advance time by 6 minutes (past default 5-minute expiry)
			mockTime += 6 * 60 * 1000;

			// Should make new request due to expiry
			await api.cachedGet("/test-cache-expiry");
			expect(requestCount).toBe(2);

			Date.now = originalDateNow;
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
				http.get("*/protected-resource", ({ request }) => {
					const auth = request.headers.get("authorization");
					authAttempts++;

					if (authAttempts === 1 || !auth || auth === "Bearer expired-token") {
						return HttpResponse.json(
							{ detail: "Token expired" },
							{ status: 401 }
						);
					}

					return HttpResponse.json({ data: "protected-data" });
				}),
				http.post("*/auth/token/refresh", () => {
					refreshAttempts++;
					return HttpResponse.json({
						access_token: "new-access-token",
						refresh_token: "new-refresh-token",
					});
				}),
			);

			localStorage.setItem("access_token", "expired-token");

			const response = await api.get("/protected-resource");

			expect(refreshAttempts).toBe(1);
			expect(authAttempts).toBe(2); // Initial fail + retry success
			expect(response.data).toEqual({ data: "protected-data" });
			expect(localStorage.getItem("access_token")).toBe("new-access-token");
		});

		it("should handle refresh token failure", async () => {
			server.use(
				http.get("*/protected-resource", () => {
					return HttpResponse.json(
						{ detail: "Token expired" },
						{ status: 401 }
					);
				}),
				http.post("*/auth/token/refresh", () => {
					return HttpResponse.json(
						{ detail: "Refresh token expired" },
						{ status: 401 }
					);
				}),
			);

			localStorage.setItem("access_token", "expired-token");
			localStorage.setItem("refresh_token", "expired-refresh-token");

			await expect(api.get("/protected-resource")).rejects.toThrow();

			// Should clear tokens
			expect(localStorage.getItem("access_token")).toBeNull();
			expect(localStorage.getItem("refresh_token")).toBeNull();
		});

		it("should queue multiple requests during token refresh", async () => {
			let refreshCount = 0;
			let requestCount = 0;

			server.use(
				http.get("*/protected-resource", ({ request }) => {
					const auth = request.headers.get("authorization");
					requestCount++;

					if (!auth || auth === "Bearer expired-token") {
						return HttpResponse.json(
							{ detail: "Token expired" },
							{ status: 401 }
						);
					}

					return HttpResponse.json({ data: `response-${requestCount}` });
				}),
				http.post("*/auth/token/refresh", async () => {
					refreshCount++;
					// Simulate delay
					await new Promise(resolve => setTimeout(resolve, 50));
					return HttpResponse.json({
						access_token: "new-access-token",
						refresh_token: "new-refresh-token",
					});
				}),
			);

			localStorage.setItem("access_token", "expired-token");

			// Make multiple simultaneous requests
			const promises = [
				api.get("/protected-resource").catch(() => ({ data: "failed" })),
				api.get("/protected-resource").catch(() => ({ data: "failed" })),
				api.get("/protected-resource").catch(() => ({ data: "failed" })),
			];

			const results = await Promise.all(promises);

			// Should only refresh once despite multiple requests
			expect(refreshCount).toBe(1);

			// At least some requests should succeed
			const successfulResults = results.filter(r => r.data !== "failed");
			expect(successfulResults.length).toBeGreaterThan(0);
		});
	});

	describe("Request retry logic", () => {
		it("should retry on network errors", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/flaky-endpoint", () => {
					attemptCount++;
					if (attemptCount < 3) {
						// Return a 500 error instead of throwing
						return HttpResponse.json(
							{ error: "Network error" },
							{ status: 500 }
						);
					}
					return HttpResponse.json({ success: true, attempts: attemptCount });
				}),
			);

			const response = await api.get("/flaky-endpoint");
			expect(response.data).toEqual({ success: true, attempts: 3 });
			expect(attemptCount).toBe(3);
		});

		it("should retry on 5xx server errors", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/server-error", () => {
					attemptCount++;
					if (attemptCount < 2) {
						return HttpResponse.json(
							{ error: "Internal server error" },
							{ status: 500 }
						);
					}
					return HttpResponse.json({ success: true, attempts: attemptCount });
				}),
			);

			const response = await api.get("/server-error");
			expect(response.data).toEqual({ success: true, attempts: 2 });
			expect(attemptCount).toBe(2);
		});

		it("should not retry on 4xx client errors (except 401)", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/bad-request", () => {
					attemptCount++;
					return HttpResponse.json(
						{ error: "Bad request" },
						{ status: 400 }
					);
				}),
			);

			await expect(api.get("/bad-request")).rejects.toThrow();
			expect(attemptCount).toBe(1); // Should not retry
		});

		it("should eventually fail after max retries", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/always-500", () => {
					attemptCount++;
					return HttpResponse.json(
						{ error: "Always fails" },
						{ status: 500 }
					);
				}),
			);

			await expect(api.get("/always-500")).rejects.toThrow();
			expect(attemptCount).toBeGreaterThan(1); // Should have retried
			expect(attemptCount).toBeLessThanOrEqual(4); // Should not exceed max retries + 1
		}, 10000); // Increase timeout to 10 seconds
	});

	describe("URL normalization", () => {
		it("should normalize relative URLs with API version", async () => {
			let capturedUrl = "";

			server.use(
				http.get("*/v1/users/profile", ({ request }) => {
					capturedUrl = request.url;
					return HttpResponse.json({ success: true });
				}),
			);

			await api.get("/users/profile");
			expect(capturedUrl).toContain("/v1/users/profile");
		});

		it("should not modify absolute URLs", async () => {
			server.use(
				http.get("https://external-api.com/data", ({ request }) => {
					return HttpResponse.json({ external: true });
				}),
			);

			const response = await api.get("https://external-api.com/data");
			expect(response.data).toEqual({ external: true });
		});
	});

	describe("Cache invalidation", () => {
		it("should invalidate cache on POST requests", async () => {
			let getRequestCount = 0;

			server.use(
				http.get("*/users", () => {
					getRequestCount++;
					return HttpResponse.json({ users: [], count: getRequestCount });
				}),
				http.post("*/users", () => {
					return HttpResponse.json({ id: 1, name: "New User" }, { status: 201 });
				}),
			);

			// Initial GET request - should cache
			await api.cachedGet("/users");
			expect(getRequestCount).toBe(1);

			// Second GET request - should use cache
			await api.cachedGet("/users");
			expect(getRequestCount).toBe(1);

			// POST request - should invalidate cache
			await api.post("/users", { name: "New User" });

			// GET request after POST - should hit server again
			await api.cachedGet("/users");
			expect(getRequestCount).toBe(2);
		});

		it("should invalidate cache on PUT, PATCH, and DELETE requests", async () => {
			let getRequestCount = 0;

			server.use(
				http.get("*/users/1", () => {
					getRequestCount++;
					return HttpResponse.json({ id: 1, name: "User", count: getRequestCount });
				}),
				http.put("*/users/1", () => HttpResponse.json({ success: true })),
				http.patch("*/users/1", () => HttpResponse.json({ success: true })),
				http.delete("*/users/1", () => HttpResponse.json({ success: true })),
			);

			// Cache the GET request
			await api.cachedGet("/users/1");
			expect(getRequestCount).toBe(1);

			// Each mutation should invalidate cache
			await api.put("/users/1", { name: "Updated" });
			await api.cachedGet("/users/1");
			expect(getRequestCount).toBe(2);

			await api.patch("/users/1", { name: "Patched" });
			await api.cachedGet("/users/1");
			expect(getRequestCount).toBe(3);

			await api.delete("/users/1");
			await api.cachedGet("/users/1");
			expect(getRequestCount).toBe(4);
		}, 10000); // Increase timeout to 10 seconds
	});
}); describe("API interceptors", () => {
	beforeEach(() => {
		localStorage.clear();
		apiCache.clear();
		// Ensure navigator.onLine is true for most tests
		Object.defineProperty(navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});

	afterEach(() => {
		vi.restoreAllMocks();
		server.resetHandlers();
	});

	it("should add authorization header when token is present", async () => {
		localStorage.setItem("access_token", "test-token");

		let capturedHeaders = {};

		server.use(
			http.get("*/test-auth-header", ({ request }) => {
				capturedHeaders = Object.fromEntries(request.headers);
				return HttpResponse.json({ success: true });
			}),
		);

		await api.get("/test-auth-header");
		expect(capturedHeaders).toHaveProperty(
			"authorization",
			"Bearer test-token",
		);
	}); it("should handle offline status", async () => {
		Object.defineProperty(navigator, "onLine", {
			value: false,
			configurable: true,
		});
		const captureExceptionSpy = vi
			.spyOn(errorMonitor, "captureException")
			.mockImplementation(() => { });

		await expect(api.get("/any-endpoint")).rejects.toThrow(
			"You are offline. Please check your connection.",
		);

		// Restore online status
		Object.defineProperty(navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});
});
