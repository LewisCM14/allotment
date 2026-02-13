// Consolidated test setup for Vitest (React + Vite)
import { beforeAll, afterAll, afterEach, vi } from "vitest";
import "@testing-library/jest-dom";
import { server } from "../src/mocks/server";
import { cleanup } from "@testing-library/react";
import React from "react";

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

// Mock globalThis.envConfig for runtime configuration in tests
globalThis.envConfig = {
    VITE_API_URL: "http://localhost:8000",
    VITE_API_VERSION: "/api/v1",
    VITE_APP_TITLE: "Allotment Test",
    VITE_CONTACT_EMAIL: "test@example.com",
    VITE_FORCE_AUTH: "false",
};

vi.stubGlobal("window", {
    ...globalThis.window, // preserve jsdom's document and all other properties
    document: globalThis.window.document, // ensure document is present
    location: {
        href: "http://localhost:3000",
        origin: "http://localhost:3000",
        protocol: "http:",
        host: "localhost:3000",
        hostname: "localhost",
        port: "3000",
        pathname: "/",
        search: "",
        hash: "",
        reload: vi.fn(),
        replace: vi.fn(),
        assign: vi.fn(),
    },
    localStorage: localStorageMock,
    navigator: {
        onLine: true,
    },
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    getComputedStyle: vi.fn().mockImplementation(() => ({
        marginLeft: '0px',
        marginRight: '0px',
        paddingLeft: '0px',
        paddingRight: '0px',
        borderLeftWidth: '0px',
        borderRightWidth: '0px',
        overflow: 'visible',
        boxSizing: 'border-box',
    })),
    matchMedia:
        globalThis.window?.matchMedia ||
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
Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });

if (globalThis.window && !globalThis.window.matchMedia) {
    globalThis.window.matchMedia = vi.fn().mockImplementation((query) => ({
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

// Mock getComputedStyle for components that need it (like react-remove-scroll-bar)
if (globalThis.window && !globalThis.window.getComputedStyle) {
    globalThis.window.getComputedStyle = vi.fn().mockImplementation(() => ({
        marginLeft: '0px',
        marginRight: '0px',
        paddingLeft: '0px',
        paddingRight: '0px',
        borderLeftWidth: '0px',
        borderRightWidth: '0px',
        overflow: 'visible',
        boxSizing: 'border-box',
        getPropertyValue: vi.fn().mockReturnValue('0px'),
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
    if (globalThis.document) {
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
            arg.includes('Warning: Can\'t perform a React state update') ||
            // Suppress Radix UI asChild prop warning (known issue with React 19)
            arg.includes('React does not recognize the `asChild` prop'))
    );

    if (!isTestingLibraryWarning) {
        originalConsoleError(...args);
    }
};

// Mock Radix UI components that are causing prototype issues in tests
vi.mock("@radix-ui/react-select", () => ({
    Root: vi.fn(({ children, onValueChange, value, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-root', ...props }, children)
    ),
    Trigger: vi.fn(({ children, ...props }) => 
        React.createElement('button', { 'data-testid': 'select-trigger', ...props }, children)
    ),
    Value: vi.fn(({ children, placeholder, ...props }) => 
        React.createElement('span', { 'data-testid': 'select-value', ...props }, children || placeholder)
    ),
    Icon: vi.fn(({ children, ...props }) => 
        React.createElement('span', { 'data-testid': 'select-icon', ...props }, children)
    ),
    Portal: vi.fn(({ children }) => children),
    Content: vi.fn(({ children, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-content', ...props }, children)
    ),
    Viewport: vi.fn(({ children, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-viewport', ...props }, children)
    ),
    Group: vi.fn(({ children, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-group', ...props }, children)
    ),
    Label: vi.fn(({ children, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-label', ...props }, children)
    ),
    Item: vi.fn(({ children, value, ...props }) => 
        React.createElement('div', { 'data-testid': 'select-item', 'data-value': value, ...props }, children)
    ),
    ItemText: vi.fn(({ children, ...props }) => 
        React.createElement('span', { 'data-testid': 'select-item-text', ...props }, children)
    ),
    ItemIndicator: vi.fn(({ children, ...props }) => 
        React.createElement('span', { 'data-testid': 'select-item-indicator', ...props }, children)
    ),
    ScrollUpButton: vi.fn(({ children, ...props }) => 
        React.createElement('button', { 'data-testid': 'select-scroll-up', ...props }, children)
    ),
    ScrollDownButton: vi.fn(({ children, ...props }) => 
        React.createElement('button', { 'data-testid': 'select-scroll-down', ...props }, children)
    ),
    Separator: vi.fn((props) => 
        React.createElement('div', { 'data-testid': 'select-separator', ...props })
    ),
}));

vi.mock("@radix-ui/react-switch", () => ({
    Root: vi.fn(({ children, checked, onCheckedChange, ...props }) => 
        React.createElement('button', { 
            'data-testid': 'switch-root', 
            'aria-checked': checked,
            onClick: () => onCheckedChange?.(!checked),
            role: 'switch',
            ...props 
        }, children)
    ),
    Thumb: vi.fn((props) => 
        React.createElement('span', { 'data-testid': 'switch-thumb', ...props })
    ),
}));

vi.mock("@radix-ui/react-dialog", () => ({
    Root: vi.fn(({ children, open, onOpenChange, ...props }) => 
        React.createElement('div', { 'data-testid': 'dialog-root', 'data-open': open, ...props }, children)
    ),
    Portal: vi.fn(({ children }) => children),
    Overlay: vi.fn((props) => 
        React.createElement('div', { 'data-testid': 'dialog-overlay', ...props })
    ),
    Content: vi.fn(({ children, ...props }) => 
        React.createElement('div', { 'data-testid': 'dialog-content', ...props }, children)
    ),
    Title: vi.fn(({ children, ...props }) => 
        React.createElement('h2', { 'data-testid': 'dialog-title', ...props }, children)
    ),
    Description: vi.fn(({ children, ...props }) => 
        React.createElement('p', { 'data-testid': 'dialog-description', ...props }, children)
    ),
    Close: vi.fn(({ children, ...props }) => 
        React.createElement('button', { 'data-testid': 'dialog-close', ...props }, children)
    ),
    Trigger: vi.fn(({ children, ...props }) => 
        React.createElement('button', { 'data-testid': 'dialog-trigger', ...props }, children)
    ),
}));

// Add global helper to identify slow-running tests
(globalThis as any).__VitestPerformanceMarks = new Map();
