import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { server } from "./src/mocks/server";

// Mock import.meta.env for consistent API URL and Version in tests
vi.stubGlobal('import.meta', {
    env: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_VERSION: '/api/v1',
    },
});

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

// Reset any request handlers that we may add during the tests
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished
afterAll(() => server.close());
