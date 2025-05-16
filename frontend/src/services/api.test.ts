import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../mocks/server";
import api, { handleApiError } from "./api";

// Mock localStorage
const localStorageMock = (() => {
	let store: Record<string, string> = {};
	return {
		getItem: (key: string) => store[key] || null,
		setItem: (key: string, value: string) => {
			store[key] = value;
		},
		removeItem: (key: string) => {
			delete store[key];
		},
		clear: () => {
			store = {};
		},
	};
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("API Service", () => {
	beforeEach(() => {
		localStorage.clear();
		vi.spyOn(console, "error").mockImplementation(() => {});
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

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
});

describe("API interceptors", () => {
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
		const originalNavigator = { ...navigator };
		Object.defineProperty(navigator, "onLine", {
			value: false,
			configurable: true,
		});

		await expect(api.get("/any-endpoint")).rejects.toThrow(
			"You are offline. Please check your connection.",
		);

		Object.defineProperty(navigator, "onLine", {
			value: originalNavigator.onLine,
		});
	});
});
