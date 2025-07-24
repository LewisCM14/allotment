// Consolidated test setup for Vitest (React + Vite)
import { beforeAll, afterAll, afterEach, vi } from "vitest";
import "@testing-library/jest-dom";
import { server } from "../src/mocks/server";
import { cleanup } from "@testing-library/react";

// Polyfill for IE event methods that React might try to use
if (typeof HTMLElement !== "undefined") {
    (HTMLElement.prototype as any).attachEvent = function (_event: string, _handler: any) { };
    (HTMLElement.prototype as any).detachEvent = function (_event: string, _handler: any) { };
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
        key: (index: number) => Object.keys(store)[index] || null,
        get length() {
            return Object.keys(store).length;
        },
    };
})();

// Mock import.meta.env for consistent API URL and Version in tests
vi.stubGlobal("import.meta", {
    env: {
        VITE_API_URL: "http://localhost:8000",
        VITE_API_VERSION: "/api/v1",
    },
});

// Mock window.envConfig for runtime configuration in tests
vi.stubGlobal("window", {
    ...global.window, // preserve jsdom's document and all other properties
    document: global.window.document, // ensure document is present
    envConfig: {
        VITE_API_URL: "http://localhost:8000",
        VITE_API_VERSION: "/api/v1",
        VITE_APP_TITLE: "Allotment Test",
        VITE_CONTACT_EMAIL: "test@example.com",
        VITE_FORCE_AUTH: "false",
    },
    localStorage: localStorageMock,
    navigator: {
        onLine: true,
    },
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    matchMedia:
        global.window?.matchMedia ||
        vi.fn().mockImplementation((query) => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: vi.fn(),
            removeListener: vi.fn(),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
        })),
});

// Set up global mocks for browser APIs
Object.defineProperty(global, "localStorage", { value: localStorageMock });

if (global.window && !global.window.matchMedia) {
    global.window.matchMedia = vi.fn().mockImplementation((query) => ({
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

// MSW server setup
beforeAll(() => {
    server.listen({
        onUnhandledRequest: "warn"
    });
});

afterEach(() => {
    // Reset MSW handlers
    server.resetHandlers();

    // Clear localStorage state
    localStorageMock.clear();

    // Clean up React Testing Library
    cleanup();

    // Reset all mocks and timers
    vi.clearAllMocks();
    vi.clearAllTimers();
    vi.useRealTimers();

    // Reset any navigator mocks
    Object.defineProperty(navigator, "onLine", {
        value: true,
        configurable: true
    });

    // Reset document body
    if (global.document) {
        document.body.innerHTML = '';
    }
});

afterAll(() => {
    server.close();
});

// Disable console errors during tests to reduce noise
const originalConsoleError = console.error;
console.error = (...args) => {
    // Filter out expected React errors during testing
    const isTestingLibraryWarning = args.some(arg =>
        typeof arg === 'string' &&
        (arg.includes('Warning: ReactDOM.render') ||
            arg.includes('Warning: An update to') ||
            arg.includes('Warning: Can\'t perform a React state update'))
    );

    if (!isTestingLibraryWarning) {
        originalConsoleError(...args);
    }
};

// Add global helper to identify slow-running tests
globalThis.__VitestPerformanceMarks = new Map();
globalThis.__VitestPerformanceMarks = new Map();
