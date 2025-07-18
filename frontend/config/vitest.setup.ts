// Mock import.meta.env for consistent API URL and Version in tests
// THIS MUST BE AT THE VERY TOP, before any other imports.
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import "@testing-library/jest-dom";

// Polyfill for IE event methods that React might try to use
if (typeof HTMLElement !== 'undefined') {
    (HTMLElement.prototype as any).attachEvent = function (event: string, handler: any) {
        if (typeof handler === 'function') {
            this.addEventListener(event.replace('on', ''), handler);
        }
    };

    (HTMLElement.prototype as any).detachEvent = function (event: string, handler: any) {
        if (typeof handler === 'function') {
            this.removeEventListener(event.replace('on', ''), handler);
        }
    };
}

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

vi.stubGlobal('import.meta', {
    env: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_VERSION: '/api/v1',
        // Add other VITE_ variables your app might need at build time or as a fallback
    },
});

// Mock window.envConfig for runtime configuration in tests
vi.stubGlobal('window', {
    ...global.window, // Preserve existing window properties if any (e.g., from jsdom)
    envConfig: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_VERSION: '/api/v1',
        VITE_APP_TITLE: 'Allotment Test',
        VITE_CONTACT_EMAIL: 'test@example.com',
        VITE_FORCE_AUTH: 'false',
    },
    // Ensure localStorage and navigator are part of this new window object
    localStorage: localStorageMock, // Use the hoisted localStorageMock
    navigator: {
        onLine: true,
    },
    // Mock window event listeners
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    matchMedia: global.window?.matchMedia || vi.fn().mockImplementation(query => ({ // Preserve existing matchMedia or mock it
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(), // deprecated
        removeListener: vi.fn(), // deprecated
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});


import { server } from "../src/mocks/server";

// Set up global mocks for browser APIs
Object.defineProperty(global, "localStorage", { value: localStorageMock });

if (global.window && !global.window.matchMedia) {
    global.window.matchMedia = vi.fn().mockImplementation(query => ({
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
