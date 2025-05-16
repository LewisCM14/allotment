// Mock import.meta.env for consistent API URL and Version in tests
// THIS MUST BE AT THE VERY TOP, before any other imports.
import { vi } from "vitest";

vi.stubGlobal('import.meta', {
    env: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_VERSION: '/api/v1',
    },
});

// Now import other modules
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./src/mocks/server";

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

// Reset any request handlers that we may add during the tests
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished
afterAll(() => server.close());
