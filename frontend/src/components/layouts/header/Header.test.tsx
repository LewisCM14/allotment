import {
	render,
	screen,
	waitFor,
	queryByAttribute,
	waitForElementToBeRemoved,
	act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Header from "./HeaderContainer";
import * as AuthContext from "@/store/auth/AuthContext";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, beforeEach, expect } from "vitest";

vi.mock("@/store/auth/AuthContext");

describe("Header", () => {
	const createMockAuthContext = (isAuthenticated: boolean) => ({
		accessToken: isAuthenticated ? "mock-token" : null,
		refreshToken: isAuthenticated ? "mock-refresh-token" : null,
		isAuthenticated,
		firstName: isAuthenticated ? "John" : null,
		user: isAuthenticated
			? {
					user_id: "1",
					user_first_name: "John",
					user_email: "test@example.com",
					isEmailVerified: true,
				}
			: null,
		login: vi.fn(),
		logout: vi.fn(),
		refreshAccessToken: vi.fn(),
	});

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("shows login link when not authenticated", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		render(
			<MemoryRouter>
				<Header />
			</MemoryRouter>,
		);
		expect(screen.getByText(/login/i)).toBeInTheDocument();
	});

	it("shows nav links when authenticated", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));
		render(
			<MemoryRouter>
				<Header />
			</MemoryRouter>,
		);
		expect(screen.getByText(/grow guides/i)).toBeInTheDocument();
		expect(screen.getByText(/families/i)).toBeInTheDocument();
		expect(screen.getByText(/public guides/i)).toBeInTheDocument();
	});

	it("opens and closes mobile menu", async () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));
		render(
			<MemoryRouter>
				<Header />
			</MemoryRouter>,
		);
		const menuBtn = screen.getByLabelText(/toggle navigation menu/i);
		await userEvent.click(menuBtn);
		// Find the mobile menu by data-testid
		const getMenu = () => screen.queryByTestId("mobile-menu");
		expect(getMenu()).toBeInTheDocument();
		// Simulate outside click to close by firing mousedown event
		act(() => {
			const mousedownEvent = new MouseEvent("mousedown", {
				bubbles: true,
				cancelable: true,
			});
			document.body.dispatchEvent(mousedownEvent);
		});
		// Wait for React to update the DOM and then check
		await new Promise((resolve) => setTimeout(resolve, 100));
		expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
	});
});
