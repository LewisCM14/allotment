/// <reference types="vitest/globals" />
import { vi, beforeEach, afterEach, describe, it, expect } from "vitest";
import type { MockInstance } from "vitest";

vi.mock("idb", () => {
	const mockPut = vi.fn();
	const mockGet = vi.fn();
	const mockDelete = vi.fn();

	return {
		openDB: vi.fn(() =>
			Promise.resolve({
				put: mockPut,
				get: mockGet,
				delete: mockDelete,
			}),
		),
		mockPut,
		mockGet,
		mockDelete,
	};
});

import {
	saveAuthToIndexedDB,
	loadAuthFromIndexedDB,
	clearAuthFromIndexedDB,
} from "./authDB";

describe("authDB", () => {
	let consoleSpy: MockInstance;
	let mockPut: MockInstance;
	let mockGet: MockInstance;
	let mockDelete: MockInstance;

	beforeEach(async () => {
		vi.clearAllMocks();
		consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

		const idbModule = (await vi.importMock("idb")) as {
			mockPut: MockInstance;
			mockGet: MockInstance;
			mockDelete: MockInstance;
		};
		mockPut = idbModule.mockPut;
		mockGet = idbModule.mockGet;
		mockDelete = idbModule.mockDelete;
	});

	afterEach(() => {
		consoleSpy.mockRestore();
	});

	describe("saveAuthToIndexedDB", () => {
		it("saves auth state to IndexedDB successfully", async () => {
			const authState = {
				access_token: "test-access",
				refresh_token: "test-refresh",
				isAuthenticated: true,
				firstName: "Test User",
			};

			mockPut.mockResolvedValue(undefined);

			await saveAuthToIndexedDB(authState);

			expect(mockPut).toHaveBeenCalledWith("auth", authState, "authState");
		});

		it("handles errors when saving to IndexedDB", async () => {
			const authState = {
				access_token: "test-access",
				refresh_token: "test-refresh",
				isAuthenticated: true,
			};

			const error = new Error("IndexedDB error");
			mockPut.mockRejectedValue(error);

			await expect(saveAuthToIndexedDB(authState)).rejects.toThrow(
				"IndexedDB error",
			);
		});
	});

	describe("loadAuthFromIndexedDB", () => {
		it("loads auth state from IndexedDB successfully", async () => {
			const storedAuth = {
				access_token: "stored-access",
				refresh_token: "stored-refresh",
				isAuthenticated: true,
				firstName: "Stored User",
			};

			mockGet.mockResolvedValue(storedAuth);

			const result = await loadAuthFromIndexedDB();

			expect(mockGet).toHaveBeenCalledWith("auth", "authState");
			expect(result).toEqual(storedAuth);
		});

		it("returns default state when no auth found in IndexedDB", async () => {
			mockGet.mockResolvedValue(undefined);

			const result = await loadAuthFromIndexedDB();

			expect(result).toEqual({
				access_token: "",
				refresh_token: "",
				isAuthenticated: false,
			});
		});

		it("handles errors when loading from IndexedDB", async () => {
			const error = new Error("IndexedDB read error");
			mockGet.mockRejectedValue(error);

			const result = await loadAuthFromIndexedDB();

			expect(consoleSpy).toHaveBeenCalledWith(
				"Error loading auth from IndexedDB:",
				error,
			);
			expect(result).toEqual({
				access_token: "",
				refresh_token: "",
				isAuthenticated: false,
			});
		});
	});

	describe("clearAuthFromIndexedDB", () => {
		it("clears auth state from IndexedDB successfully", async () => {
			mockDelete.mockResolvedValue(undefined);

			await clearAuthFromIndexedDB();

			expect(mockDelete).toHaveBeenCalledWith("auth", "authState");
		});

		it("handles errors when clearing IndexedDB", async () => {
			const error = new Error("IndexedDB delete error");
			mockDelete.mockRejectedValue(error);

			await expect(clearAuthFromIndexedDB()).rejects.toThrow(
				"IndexedDB delete error",
			);
		});
	});
});
