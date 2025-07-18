import { afterAll, afterEach, beforeAll, vi } from "vitest";
import "@testing-library/jest-dom";
import { server } from "./mocks/server";

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

// Mock global window object before any test runs
beforeAll(() => {
	// Mock window methods that components might use
	Object.defineProperty(window, "addEventListener", {
		value: vi.fn(),
		writable: true,
		configurable: true,
	});
	Object.defineProperty(window, "removeEventListener", {
		value: vi.fn(),
		writable: true,
		configurable: true,
	});
	Object.defineProperty(window, "localStorage", {
		value: localStorageMock,
		writable: true,
		configurable: true,
	});

	// Start MSW server
	server.listen({ onUnhandledRequest: "warn" });
});

// Clean up after each test
afterEach(() => {
	server.resetHandlers();
	localStorageMock.clear();
});

// Clean up after all tests
afterAll(() => server.close());
