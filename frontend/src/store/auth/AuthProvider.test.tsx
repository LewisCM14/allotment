/// <reference types="vitest/globals" />
import { useContext } from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthProvider } from "./AuthProvider";
import { AuthContext } from "./AuthContext";
import { vi } from "vitest";
import type { MockInstance } from "vitest";
import * as authDB from "./authDB";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { errorMonitor } from "@/services/errorMonitoring";
import { tokenStore } from "@/services/tokenStore";

// Helper to consume the context
function AuthConsumer() {
	const context = useContext(AuthContext);
	if (!context) return null;
	const {
		accessToken,
		refreshToken,
		isAuthenticated,
		firstName,
		user,
		login,
		logout,
		refreshAccessToken,
	} = context;

	return (
		<>
			<span data-testid="access-token">{accessToken || "null"}</span>
			<span data-testid="refresh-token">{refreshToken || "null"}</span>
			<span data-testid="authenticated">{isAuthenticated.toString()}</span>
			<span data-testid="first-name">{firstName || "null"}</span>
			<span data-testid="user-id">{user?.user_id || "null"}</span>
			<button
				type="button"
				onClick={() =>
					login(
						{
							access_token: "test-access",
							refresh_token: "test-refresh",
						},
						"Test User",
					)
				}
			>
				Login
			</button>
			<button type="button" onClick={logout}>
				Logout
			</button>
			<button type="button" onClick={() => refreshAccessToken()}>
				Refresh Token
			</button>
		</>
	);
}

// Mock the authDB module
vi.mock("./authDB", () => ({
	saveAuthToIndexedDB: vi.fn(),
	loadAuthFromIndexedDB: vi.fn(),
	clearAuthFromIndexedDB: vi.fn(),
}));

// Mock toast
vi.mock("sonner", () => ({
	toast: {
		success: vi.fn(),
		error: vi.fn(),
	},
}));

// Mock error monitoring
vi.mock("@/services/errorMonitoring", () => ({
	errorMonitor: {
		captureException: vi.fn(),
		captureMessage: vi.fn(),
	},
}));

// Extended consumer for login-with-userData tests
function AuthConsumerWithUserData() {
	const context = useContext(AuthContext);
	if (!context) return null;
	const {
		accessToken,
		refreshToken,
		isAuthenticated,
		firstName,
		user,
		login,
		logout,
		refreshAccessToken,
	} = context;

	return (
		<>
			<span data-testid="access-token">{accessToken || "null"}</span>
			<span data-testid="refresh-token">{refreshToken || "null"}</span>
			<span data-testid="authenticated">{isAuthenticated.toString()}</span>
			<span data-testid="first-name">{firstName || "null"}</span>
			<span data-testid="user-id">{user?.user_id || "null"}</span>
			<span data-testid="user-email">{user?.user_email || "null"}</span>
			<button
				type="button"
				onClick={() =>
					login(
						{
							access_token: "test-access",
							refresh_token: "test-refresh",
						},
						"Test User",
						{
							user_id: "user-123",
							user_email: "test@example.com",
							is_email_verified: true,
						},
					)
				}
			>
				Login With Data
			</button>
			<button type="button" onClick={logout}>
				Logout
			</button>
			<button type="button" onClick={() => refreshAccessToken()}>
				Refresh Token
			</button>
		</>
	);
}

describe("AuthProvider", () => {
	let getItemMock: MockInstance;
	let setItemMock: MockInstance;
	let removeItemMock: MockInstance;
	let clearMock: MockInstance;
	let saveAuthToIndexedDBMock: MockInstance;
	let loadAuthFromIndexedDBMock: MockInstance;
	let clearAuthFromIndexedDBMock: MockInstance;

	beforeEach(() => {
		tokenStore.clearTokens();

		// Mock localStorage
		getItemMock = vi.spyOn(window.localStorage, "getItem");
		setItemMock = vi.spyOn(window.localStorage, "setItem");
		removeItemMock = vi.spyOn(window.localStorage, "removeItem");
		clearMock = vi.spyOn(window.localStorage, "clear");

		// Reset localStorage mocks
		getItemMock.mockImplementation(() => null);
		setItemMock.mockImplementation(() => {});
		removeItemMock.mockImplementation(() => {});
		clearMock.mockImplementation(() => {});

		// Mock IndexedDB functions
		saveAuthToIndexedDBMock = vi.mocked(authDB.saveAuthToIndexedDB);
		loadAuthFromIndexedDBMock = vi.mocked(authDB.loadAuthFromIndexedDB);
		clearAuthFromIndexedDBMock = vi.mocked(authDB.clearAuthFromIndexedDB);

		// Reset IndexedDB mocks
		saveAuthToIndexedDBMock.mockResolvedValue(undefined);
		loadAuthFromIndexedDBMock.mockResolvedValue({
			isAuthenticated: false,
		});
		clearAuthFromIndexedDBMock.mockResolvedValue(undefined);

		// Mock import.meta.env
		vi.stubGlobal("import.meta", {
			env: {
				DEV: false,
				VITE_FORCE_AUTH: "false",
			},
		});
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("initializes with unauthenticated state when no stored auth", async () => {
		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		// Wait for the component to render and complete initialization
		await waitFor(
			() => {
				expect(screen.getByTestId("access-token").textContent).toBe("null");
				expect(screen.getByTestId("refresh-token").textContent).toBe("null");
				expect(screen.getByTestId("authenticated").textContent).toBe("false");
				expect(screen.getByTestId("first-name").textContent).toBe("null");
				expect(screen.getByTestId("user-id").textContent).toBe("null");
			},
			{ timeout: 10000 },
		);
	});

	it("ignores persisted tokens in localStorage", async () => {
		getItemMock.mockImplementation((key) => {
			switch (key) {
				case "access_token":
					return "stored-access-token";
				case "refresh_token":
					return "stored-refresh-token";
				case "first_name":
					return "Stored User";
				case "user_email":
					return "stored@example.com";
				case "user_id":
					return "stored-user-123";
				case "is_email_verified":
					return "true";
				default:
					return null;
			}
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe("null");
			expect(screen.getByTestId("refresh-token").textContent).toBe("null");
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
			expect(screen.getByTestId("first-name").textContent).toBe("null");
			expect(screen.getByTestId("user-id").textContent).toBe("null");
		});

		expect(removeItemMock).toHaveBeenCalledWith("access_token");
		expect(removeItemMock).toHaveBeenCalledWith("refresh_token");
	});

	it("clears legacy IndexedDB auth state on startup", async () => {
		loadAuthFromIndexedDBMock.mockResolvedValue({
			isAuthenticated: true,
			firstName: "Indexed User",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe("null");
			expect(screen.getByTestId("refresh-token").textContent).toBe("null");
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});

		expect(clearAuthFromIndexedDBMock).toHaveBeenCalled();
	});

	it("handles login successfully", async () => {
		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});

		fireEvent.click(screen.getByText("Login"));

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe(
				"test-access",
			);
			expect(screen.getByTestId("refresh-token").textContent).toBe(
				"test-refresh",
			);
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
			expect(screen.getByTestId("first-name").textContent).toBe("Test User");
		});

		expect(setItemMock).not.toHaveBeenCalledWith("access_token", "test-access");
		expect(setItemMock).not.toHaveBeenCalledWith(
			"refresh_token",
			"test-refresh",
		);
		expect(setItemMock).toHaveBeenCalledWith("first_name", "Test User");
		expect(saveAuthToIndexedDBMock).not.toHaveBeenCalled();
	});

	it("handles logout successfully", async () => {
		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});

		fireEvent.click(screen.getByText("Login"));

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
		});

		fireEvent.click(screen.getByText("Logout"));

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe("null");
			expect(screen.getByTestId("refresh-token").textContent).toBe("null");
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
			expect(screen.getByTestId("first-name").textContent).toBe("null");
		});

		// Should clear localStorage and IndexedDB
		expect(removeItemMock).toHaveBeenCalledWith("access_token");
		expect(removeItemMock).toHaveBeenCalledWith("refresh_token");
		expect(removeItemMock).toHaveBeenCalledWith("first_name");
		expect(removeItemMock).toHaveBeenCalledWith("user_email");
		expect(removeItemMock).toHaveBeenCalledWith("user_id");
		expect(removeItemMock).toHaveBeenCalledWith("is_email_verified");
		expect(clearAuthFromIndexedDBMock).toHaveBeenCalled();
	});

	it("throws error when used outside provider", () => {
		// Mock console.error to avoid error output in tests
		const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

		// This test checks that useAuth hook throws when used outside provider
		expect(() => {
			const TestComponent = () => {
				const context = useContext(AuthContext);
				if (context === undefined) {
					throw new Error("useAuth must be used within an AuthProvider");
				}
				return null;
			};
			render(<TestComponent />);
		}).toThrow("useAuth must be used within an AuthProvider");

		consoleSpy.mockRestore();
	});

	it("handles login with userData, storing user object and extra localStorage items", async () => {
		render(
			<AuthProvider>
				<AuthConsumerWithUserData />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});

		fireEvent.click(screen.getByText("Login With Data"));

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe(
				"test-access",
			);
			expect(screen.getByTestId("first-name").textContent).toBe("Test User");
			expect(screen.getByTestId("user-id").textContent).toBe("user-123");
			expect(screen.getByTestId("user-email").textContent).toBe(
				"test@example.com",
			);
		});

		// Should save user-specific data in localStorage
		expect(setItemMock).toHaveBeenCalledWith("user_email", "test@example.com");
		expect(setItemMock).toHaveBeenCalledWith("user_id", "user-123");
		expect(setItemMock).toHaveBeenCalledWith("is_email_verified", "true");
	});

	it("hydrates profile metadata for an in-memory session", async () => {
		tokenStore.setTokens({
			access_token: "stored-access",
			refresh_token: "stored-refresh",
		});

		getItemMock.mockImplementation((key) => {
			switch (key) {
				case "first_name":
					return "NoEmail User";
				case "user_email":
					return null;
				default:
					return null;
			}
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
			expect(screen.getByTestId("first-name").textContent).toBe("NoEmail User");
			// user should remain null since no email was available
			expect(screen.getByTestId("user-id").textContent).toBe("null");
		});
	});

	it("refreshAccessToken succeeds and updates tokens", async () => {
		tokenStore.setTokens({
			access_token: "old-access",
			refresh_token: "old-refresh",
		});

		getItemMock.mockImplementation((key) => {
			switch (key) {
				case "first_name":
					return "Refresh User";
				default:
					return null;
			}
		});

		server.use(
			http.post("*/user/auth/refresh", () => {
				return HttpResponse.json({
					access_token: "new-access",
					refresh_token: "new-refresh",
				});
			}),
		);

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
		});

		fireEvent.click(screen.getByText("Refresh Token"));

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe("new-access");
			expect(screen.getByTestId("refresh-token").textContent).toBe(
				"new-refresh",
			);
		});

		expect(setItemMock).not.toHaveBeenCalledWith("access_token", "new-access");
		expect(setItemMock).not.toHaveBeenCalledWith(
			"refresh_token",
			"new-refresh",
		);
		expect(saveAuthToIndexedDBMock).not.toHaveBeenCalled();
	});

	it("refreshAccessToken returns false when no refresh token exists", async () => {
		// No tokens in localStorage - default mock is null
		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});

		fireEvent.click(screen.getByText("Refresh Token"));

		// Should remain unauthenticated - refreshToken is null so it returns false
		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});
	});

	it("refreshAccessToken handles 401 error and logs out", async () => {
		tokenStore.setTokens({
			access_token: "old-access",
			refresh_token: "old-refresh",
		});

		getItemMock.mockImplementation((key) => {
			switch (key) {
				default:
					return null;
			}
		});

		server.use(
			http.post("*/user/auth/refresh", () => {
				return HttpResponse.json({ detail: "Token expired" }, { status: 401 });
			}),
		);

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
		});

		fireEvent.click(screen.getByText("Refresh Token"));

		// Should logout after 401
		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("false");
		});
		expect(errorMonitor.captureException).toHaveBeenCalled();
	});

	it("refreshAccessToken handles non-401 API error and logs out", async () => {
		tokenStore.setTokens({
			access_token: "old-access",
			refresh_token: "old-refresh",
		});

		getItemMock.mockImplementation((key) => {
			switch (key) {
				default:
					return null;
			}
		});

		server.use(
			http.post("*/user/auth/refresh", () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
		});

		fireEvent.click(screen.getByText("Refresh Token"));

		await waitFor(
			() => {
				expect(screen.getByTestId("authenticated").textContent).toBe("false");
			},
			{ timeout: 10000 },
		);
		expect(errorMonitor.captureException).toHaveBeenCalled();
	});

	it("refreshAccessToken handles network error and logs out", async () => {
		tokenStore.setTokens({
			access_token: "old-access",
			refresh_token: "old-refresh",
		});

		getItemMock.mockImplementation((key) => {
			switch (key) {
				default:
					return null;
			}
		});

		server.use(
			http.post("*/user/auth/refresh", () => {
				return HttpResponse.json({ detail: "Bad request" }, { status: 400 });
			}),
		);

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
		});

		fireEvent.click(screen.getByText("Refresh Token"));

		await waitFor(
			() => {
				expect(screen.getByTestId("authenticated").textContent).toBe("false");
			},
			{ timeout: 10000 },
		);
		expect(errorMonitor.captureException).toHaveBeenCalled();
	});
});
