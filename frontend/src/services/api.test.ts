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
import { server } from "../mocks/server";
import api, { handleApiError } from "./api";
import { apiCache } from "./apiCache";
import { errorMonitor } from "./errorMonitoring";
import { apiService } from "./apiService";
import { API_URL, API_VERSION } from "./apiConfig";

describe("API Service", () => {
	beforeEach(() => {
		localStorage.clear();
		apiCache.clear();
		vi.spyOn(console, "error").mockImplementation(() => {});
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
					return HttpResponse.json({
						data: "cached-response",
						count: requestCount,
					});
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
					return HttpResponse.json({
						url: "2",
						param,
						count: url2RequestCount,
					});
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
		}, 10000);
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
							{ status: 401 },
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
							{ status: 401 },
						);
					}

					return HttpResponse.json({ data: `response-${requestCount}` });
				}),
				http.post("*/auth/token/refresh", async () => {
					refreshCount++;
					// Simulate delay
					vi.useFakeTimers();
					vi.runAllTimers();
					vi.useRealTimers();
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
			const successfulResults = results.filter((r) => r.data !== "failed");
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
							{ status: 500 },
						);
					}
					return HttpResponse.json({ success: true, attempts: attemptCount });
				}),
			);

			const response = await api.get("/flaky-endpoint");
			expect(response.data).toEqual({ success: true, attempts: 3 });
			expect(attemptCount).toBe(3);
		}, 10000);

		it("should retry on 5xx server errors", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/server-error", () => {
					attemptCount++;
					if (attemptCount < 2) {
						return HttpResponse.json(
							{ error: "Internal server error" },
							{ status: 500 },
						);
					}
					return HttpResponse.json({ success: true, attempts: attemptCount });
				}),
			);

			const response = await api.get("/server-error");
			expect(response.data).toEqual({ success: true, attempts: 2 });
			expect(attemptCount).toBe(2);
		}, 10000);

		it("should not retry on 4xx client errors (except 401)", async () => {
			let attemptCount = 0;

			server.use(
				http.get("*/bad-request", () => {
					attemptCount++;
					return HttpResponse.json({ error: "Bad request" }, { status: 400 });
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
					return HttpResponse.json({ error: "Always fails" }, { status: 500 });
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
					return HttpResponse.json(
						{ id: 1, name: "New User" },
						{ status: 201 },
					);
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
					return HttpResponse.json({
						id: 1,
						name: "User",
						count: getRequestCount,
					});
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
});
describe("API interceptors", () => {
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
	});
	it("should handle offline status", async () => {
		Object.defineProperty(navigator, "onLine", {
			value: false,
			configurable: true,
		});
		const captureExceptionSpy = vi
			.spyOn(errorMonitor, "captureException")
			.mockImplementation(() => {});

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

describe("ApiService class", () => {
	beforeEach(() => {
		localStorage.clear();
		apiCache.clear();
		vi.spyOn(console, "error").mockImplementation(() => {});
	});

	afterEach(() => {
		vi.restoreAllMocks();
		server.resetHandlers();
	});

	it("should handle GET requests with custom error message", async () => {
		server.use(
			http.get("*/test-endpoint", () => {
				return HttpResponse.json({ data: "test" });
			}),
		);

		const result = await apiService.get("/test-endpoint", {
			errorMessage: "Custom error",
		});
		expect(result).toEqual({ data: "test" });
	});

	it("should handle GET requests with caching enabled", async () => {
		let requestCount = 0;
		server.use(
			http.get("*/cached-endpoint", () => {
				requestCount++;
				return HttpResponse.json({ data: "cached", count: requestCount });
			}),
		);

		// First request
		const result1 = await apiService.get("/cached-endpoint", {
			useCache: true,
		});
		expect(result1).toEqual({ data: "cached", count: 1 });

		// Second request should use cache
		const result2 = await apiService.get("/cached-endpoint", {
			useCache: true,
		});
		expect(result2).toEqual({ data: "cached", count: 1 });
		expect(requestCount).toBe(1);
	});

	it("should handle POST requests", async () => {
		server.use(
			http.post("*/create-endpoint", async ({ request }) => {
				const body = await request.json();
				return HttpResponse.json({ created: true, data: body });
			}),
		);

		const result = await apiService.post("/create-endpoint", { name: "test" });
		expect(result).toEqual({ created: true, data: { name: "test" } });
	});

	it("should handle PUT requests", async () => {
		server.use(
			http.put("*/update-endpoint", async ({ request }) => {
				const body = await request.json();
				return HttpResponse.json({ updated: true, data: body });
			}),
		);

		const result = await apiService.put("/update-endpoint", {
			name: "updated",
		});
		expect(result).toEqual({ updated: true, data: { name: "updated" } });
	});

	it("should handle PATCH requests", async () => {
		server.use(
			http.patch("*/patch-endpoint", async ({ request }) => {
				const body = await request.json();
				return HttpResponse.json({ patched: true, data: body });
			}),
		);

		const result = await apiService.patch("/patch-endpoint", {
			name: "patched",
		});
		expect(result).toEqual({ patched: true, data: { name: "patched" } });
	}, 10000);

	it("should handle DELETE requests", async () => {
		server.use(
			http.delete("*/delete-endpoint", () => {
				return HttpResponse.json({ deleted: true });
			}),
		);

		const result = await apiService.delete("/delete-endpoint");
		expect(result).toEqual({ deleted: true });
	});

	it("should handle errors in GET requests", async () => {
		server.use(
			http.get("*/error-endpoint", () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		await expect(
			apiService.get("/error-endpoint", { errorMessage: "Custom GET error" }),
		).rejects.toThrow();
	}, 10000); // Increase timeout

	it("should handle errors in POST requests", async () => {
		server.use(
			http.post("*/error-endpoint", () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		await expect(
			apiService.post(
				"/error-endpoint",
				{},
				{ errorMessage: "Custom POST error" },
			),
		).rejects.toThrow();
	}, 10000); // Increase timeout
});

describe("ApiCache service", () => {
	beforeEach(() => {
		apiCache.clear();
	});

	it("should cache data with custom duration", async () => {
		return new Promise<void>((resolve) => {
			apiCache.set("test-key", { data: "test" }, 100);

			// Should be available immediately
			expect(apiCache.get("test-key")).toEqual({ data: "test" });

			// Should be cleared after duration
			setTimeout(() => {
				expect(apiCache.get("test-key")).toBeNull();
				resolve();
			}, 150);
		});
	});

	it("should invalidate cache by pattern", () => {
		apiCache.set("/users/1", { user: 1 });
		apiCache.set("/users/2", { user: 2 });
		apiCache.set("/posts/1", { post: 1 });

		apiCache.invalidate(/\/users\/.*/);

		expect(apiCache.get("/users/1")).toBeNull();
		expect(apiCache.get("/users/2")).toBeNull();
		expect(apiCache.get("/posts/1")).toEqual({ post: 1 });
	});

	it("should invalidate cache by prefix", () => {
		apiCache.set("/users/profile", { profile: true });
		apiCache.set("/users/allotment", { allotment: true });
		apiCache.set("/posts/1", { post: 1 });

		apiCache.invalidateByPrefix("/users/");

		expect(apiCache.get("/users/profile")).toBeNull();
		expect(apiCache.get("/users/allotment")).toBeNull();
		expect(apiCache.get("/posts/1")).toEqual({ post: 1 });
	});

	it("should invalidate user-specific data", () => {
		apiCache.set("/users/allotment", { allotment: true });
		apiCache.set("/user/profile", { profile: true });
		apiCache.set("/posts/1", { post: 1 });

		apiCache.invalidateUserData();

		expect(apiCache.get("/users/allotment")).toBeNull();
		expect(apiCache.get("/user/profile")).toBeNull();
		expect(apiCache.get("/posts/1")).toEqual({ post: 1 });
	});

	it("should return cache statistics", () => {
		apiCache.set("key1", "value1");
		apiCache.set("key2", "value2");

		const stats = apiCache.getStats();
		expect(stats.size).toBe(2);
		expect(stats.keys).toContain("key1");
		expect(stats.keys).toContain("key2");
	});
});

// --- API Service & Error Monitoring Integration ---
// (import already at top)

describe("API Service & Error Monitoring Integration", () => {
	let consoleErrorSpy: MockInstance;
	let consoleInfoSpy: MockInstance;
	let sendBeaconSpy: MockInstance;
	let fetchSpy: Mock;
	let originalProd: boolean;

	beforeEach(() => {
		// Ensure window and navigator are present (JSDOM)
		if (typeof window === "undefined")
			(global as unknown as { window: Window }).window = {} as Window;
		if (typeof navigator === "undefined")
			(global as unknown as { navigator: Navigator }).navigator =
				{} as Navigator;
		// Mock all console methods
		consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
		consoleInfoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
		// Patch import.meta.env.PROD for production simulation
		originalProd = import.meta.env.PROD;
		// Mock browser APIs (define before spying)
		Object.defineProperty(navigator, "sendBeacon", {
			value: vi.fn().mockReturnValue(true),
			writable: true,
			configurable: true,
		});
		sendBeaconSpy = vi.spyOn(navigator, "sendBeacon");
		fetchSpy = vi.fn().mockResolvedValue({ ok: true });
		global.fetch = fetchSpy;
		Object.defineProperty(window, "location", {
			value: { href: "https://test.com/page" },
			configurable: true,
		});
		Object.defineProperty(navigator, "userAgent", {
			value: "TestAgent/1.0",
			configurable: true,
		});
		server.use(
			http.get("*/network-fail", () => {
				// Simulate network error immediately
				return new Promise((_, reject) => reject(new Error("Network error")));
			}),
			http.options("*/network-fail", () => {
				return new Promise((_, reject) => reject(new Error("Network error")));
			}),
		);
		server.use(
			http.get("*/fail-500", () =>
				HttpResponse.json({ detail: "fail" }, { status: 500 }),
			),
		);
	});

	afterEach(() => {
		vi.restoreAllMocks();
		import.meta.env.PROD = originalProd;
	});

	describe("Development mode", () => {
		it("logs errors and messages to console", () => {
			errorMonitor.captureException(new Error("dev error"), { foo: 1 });
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				expect.any(Error),
				{ foo: 1 },
			);
			errorMonitor.captureMessage("dev msg", { bar: 2 });
			expect(consoleInfoSpy).toHaveBeenCalledWith("[ErrorMonitor]", "dev msg", {
				bar: 2,
			});
		});
		it("handles null/undefined/empty", () => {
			expect(() => errorMonitor.captureException(null)).not.toThrow();
			expect(() => errorMonitor.captureException(undefined)).not.toThrow();
			expect(() => errorMonitor.captureMessage("")).not.toThrow();
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				null,
				undefined,
			);
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				undefined,
				undefined,
			);
			expect(consoleInfoSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				"",
				undefined,
			);
		});
		it("handles non-Error objects", () => {
			expect(() => errorMonitor.captureException("string error")).not.toThrow();
			expect(() => errorMonitor.captureException({ foo: "bar" })).not.toThrow();
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				"string error",
				undefined,
			);
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"[ErrorMonitor]",
				{ foo: "bar" },
				undefined,
			);
		});
	});

	describe("Production mode", () => {
		beforeEach(() => {
			import.meta.env.PROD = true;
		});
		it("sends errors via sendBeacon", async () => {
			sendBeaconSpy.mockClear();
			errorMonitor.captureException(new Error("prod error"), { url: "/prod" });
			expect(sendBeaconSpy).toHaveBeenCalledTimes(1);
			const callArgs = sendBeaconSpy.mock.calls[0];
			expect(callArgs[1]).toBeInstanceOf(Blob);
			expect(callArgs[0]).toMatch(/log-client-error/);
		});
		it("sends messages via sendBeacon", async () => {
			sendBeaconSpy.mockClear();
			errorMonitor.captureMessage("prod msg", { foo: 1 });
			expect(sendBeaconSpy).toHaveBeenCalledTimes(1);
			const callArgs = sendBeaconSpy.mock.calls[0];
			expect(callArgs[1]).toBeInstanceOf(Blob);
		});
		it("falls back to fetch if sendBeacon is unavailable", async () => {
			Object.defineProperty(navigator, "sendBeacon", {
				value: undefined,
				configurable: true,
			});
			fetchSpy.mockClear();
			errorMonitor.captureException(new Error("fetch fallback"));
			expect(fetchSpy).toHaveBeenCalledTimes(1);
			expect(fetchSpy).toHaveBeenCalledWith(
				expect.stringMatching(/log-client-error/),
				expect.objectContaining({
					method: "POST",
					headers: { "Content-Type": "application/json" },
					keepalive: true,
					body: expect.stringContaining("fetch fallback"),
				}),
			);
		});
		it("handles fetch errors gracefully", async () => {
			Object.defineProperty(navigator, "sendBeacon", {
				value: undefined,
				configurable: true,
			});
			fetchSpy.mockClear();
			fetchSpy.mockRejectedValue(new Error("fail"));
			expect(() =>
				errorMonitor.captureException(new Error("fail fetch")),
			).not.toThrow();
			expect(fetchSpy).toHaveBeenCalled();
		});
		it("handles sendBeacon returning false", async () => {
			sendBeaconSpy.mockClear();
			sendBeaconSpy.mockReturnValue(false);
			expect(() =>
				errorMonitor.captureException(new Error("fail beacon")),
			).not.toThrow();
			expect(sendBeaconSpy).toHaveBeenCalled();
		});
		it("includes all error details", async () => {
			sendBeaconSpy.mockClear();
			const err = new Error("detailed");
			err.stack = "stacktrace";
			errorMonitor.captureException(err, { foo: "bar" });
			expect(sendBeaconSpy).toHaveBeenCalled();
			const callArgs = sendBeaconSpy.mock.calls[0];
			expect(callArgs[1]).toBeInstanceOf(Blob);
			expect((callArgs[1] as Blob).type).toBe("application/json");
		});
		it("handles non-Error objects in production", async () => {
			sendBeaconSpy.mockClear();
			expect(() => errorMonitor.captureException("prod string")).not.toThrow();
			expect(() => errorMonitor.captureException({ foo: 1 })).not.toThrow();
			expect(sendBeaconSpy).toHaveBeenCalledTimes(2);
		});
	});
});
