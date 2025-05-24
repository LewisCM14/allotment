// Mock import.meta.env for consistent API URL and Version in tests
// THIS MUST BE AT THE VERY TOP, before any other imports.
import { afterAll, afterEach, beforeAll, vi } from "vitest";

vi.stubGlobal('import.meta', {
    env: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_VERSION: '/api/v1',
    },
});

import { server } from "../src/mocks/server";

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
        get length() {
            return Object.keys(store).length;
        },
        key: (index: number) => {
            const keys = Object.keys(store);
            return keys[index] || null;
        }
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
            matchMedia: vi.fn().mockImplementation(query => ({
                matches: false,
                media: query,
                onchange: null,
                addListener: vi.fn(),
                removeListener: vi.fn(),
                addEventListener: vi.fn(),
                removeEventListener: vi.fn(),
                dispatchEvent: vi.fn(),
            })),
        },
        writable: true
    });
} else {
    // Ensure matchMedia is mocked even if window exists (e.g. in jsdom)
    window.matchMedia = window.matchMedia || vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    }));
}


// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));

// Reset any request handlers and clear localStorage that we may add during the tests
afterEach(() => {
    server.resetHandlers();
    localStorageMock.clear();
});

// Clean up after the tests are finished
afterAll(() => server.close());
