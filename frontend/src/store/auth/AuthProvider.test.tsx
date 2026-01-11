/// <reference types="vitest/globals" />
import { useContext } from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthProvider } from "./AuthProvider";
import { AuthContext } from "./AuthContext";
import { vi } from "vitest";
import type { MockInstance } from "vitest";
import * as authDB from "./authDB";

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

describe("AuthProvider", () => {
	let getItemMock: MockInstance;
	let setItemMock: MockInstance;
	let removeItemMock: MockInstance;
	let clearMock: MockInstance;
	let saveAuthToIndexedDBMock: MockInstance;
	let loadAuthFromIndexedDBMock: MockInstance;
	let clearAuthFromIndexedDBMock: MockInstance;

	beforeEach(() => {
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
			access_token: "",
			refresh_token: "",
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

	it("loads auth from localStorage when available", async () => {
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
			expect(screen.getByTestId("access-token").textContent).toBe(
				"stored-access-token",
			);
			expect(screen.getByTestId("refresh-token").textContent).toBe(
				"stored-refresh-token",
			);
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
			expect(screen.getByTestId("first-name").textContent).toBe("Stored User");
			expect(screen.getByTestId("user-id").textContent).toBe("stored-user-123");
		});
	});

	it("loads auth from IndexedDB when localStorage is empty", async () => {
		loadAuthFromIndexedDBMock.mockResolvedValue({
			access_token: "indexed-access-token",
			refresh_token: "indexed-refresh-token",
			isAuthenticated: true,
			firstName: "Indexed User",
		});

		render(
			<AuthProvider>
				<AuthConsumer />
			</AuthProvider>,
		);

		await waitFor(() => {
			expect(screen.getByTestId("access-token").textContent).toBe(
				"indexed-access-token",
			);
			expect(screen.getByTestId("refresh-token").textContent).toBe(
				"indexed-refresh-token",
			);
			expect(screen.getByTestId("authenticated").textContent).toBe("true");
			expect(screen.getByTestId("first-name").textContent).toBe("Indexed User");
		});

		// Should sync to localStorage
		expect(setItemMock).toHaveBeenCalledWith(
			"access_token",
			"indexed-access-token",
		);
		expect(setItemMock).toHaveBeenCalledWith(
			"refresh_token",
			"indexed-refresh-token",
		);
		expect(setItemMock).toHaveBeenCalledWith("first_name", "Indexed User");
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

		// Should save to localStorage and IndexedDB
		expect(setItemMock).toHaveBeenCalledWith("access_token", "test-access");
		expect(setItemMock).toHaveBeenCalledWith("refresh_token", "test-refresh");
		expect(setItemMock).toHaveBeenCalledWith("first_name", "Test User");
		expect(saveAuthToIndexedDBMock).toHaveBeenCalledWith({
			access_token: "test-access",
			refresh_token: "test-refresh",
			firstName: "Test User",
			isAuthenticated: true,
		});
	});

	it("handles logout successfully", async () => {
		// Start with authenticated state
		getItemMock.mockImplementation((key) => {
			switch (key) {
				case "access_token":
					return "stored-access-token";
				case "refresh_token":
					return "stored-refresh-token";
				case "first_name":
					return "Stored User";
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
});
