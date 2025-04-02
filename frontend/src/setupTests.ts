import { afterAll, afterEach, beforeAll } from "vitest";
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

// Set up global mocks for browser APIs
Object.defineProperty(global, "localStorage", { value: localStorageMock });

// Create a minimal window mock if needed by your code
if (typeof window === "undefined") {
	Object.defineProperty(global, "window", {
		value: {
			navigator: {
				onLine: true,
			},
			localStorage: localStorageMock,
		},
	});
}

// Set up MSW
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => {
	server.resetHandlers();
	localStorageMock.clear();
});
afterAll(() => server.close());
