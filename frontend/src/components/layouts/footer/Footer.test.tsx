import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Footer from "./FooterContainer";
import * as AuthContext from "@/store/auth/AuthContext";
import * as ThemeContext from "@/store/theme/ThemeContext";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, beforeEach, expect } from "vitest";

vi.mock("@/store/auth/AuthContext");
vi.mock("@/store/theme/ThemeContext");
vi.mock("@/features/auth/hooks/useLogout", () => ({
	useLogout: vi.fn(),
}));

// Mock the ToggleSwitch component to avoid Radix UI issues in tests
vi.mock("@/components/ui/ToggleSwitch", () => ({
	ToggleSwitch: ({
		checked,
		onCheckedChange,
	}: {
		checked: boolean;
		onCheckedChange: () => void;
	}) => (
		<input
			type="checkbox"
			role="switch"
			aria-checked={checked}
			checked={checked}
			onChange={onCheckedChange}
		/>
	),
}));

describe("Footer", () => {
	const mockLogout = vi.fn();
	const mockToggleTheme = vi.fn();

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

	beforeEach(async () => {
		vi.clearAllMocks();
		mockLogout.mockResolvedValue(undefined);

		// Mock useLogout hook
		const { useLogout } = await import("@/features/auth/hooks/useLogout");
		vi.mocked(useLogout).mockReturnValue(mockLogout);

		// Default theme mock
		vi.mocked(ThemeContext.useTheme).mockReturnValue({
			theme: "light",
			toggleTheme: mockToggleTheme,
		});
	});

	it("shows theme toggle and contact link when not authenticated", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		// Should show theme toggle and contact link
		expect(screen.getByRole("switch")).toBeInTheDocument();
		expect(screen.getByText(/contact/i)).toBeInTheDocument();
		expect(screen.getByText(/© \d{4}/)).toBeInTheDocument();

		// Should not show user menu button when not authenticated
		expect(
			screen.queryByLabelText(/toggle user menu/i),
		).not.toBeInTheDocument();
	});

	it("shows user menu button when authenticated", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		// Should show user menu button when authenticated
		expect(screen.getByLabelText(/toggle user menu/i)).toBeInTheDocument();
		expect(screen.getByRole("switch")).toBeInTheDocument();
		expect(screen.getByText(/contact/i)).toBeInTheDocument();
	});

	it("opens and closes user menu", async () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const menuBtn = screen.getByLabelText(/toggle user menu/i);
		await userEvent.click(menuBtn);

		// Menu should be open and show nav links
		expect(screen.getByText(/profile/i)).toBeInTheDocument();
		expect(screen.getByText(/allotment/i)).toBeInTheDocument();
		expect(screen.getByText(/preferences/i)).toBeInTheDocument();
		expect(screen.getByText(/notifications/i)).toBeInTheDocument();
		expect(screen.getByText(/sign out/i)).toBeInTheDocument();

		// Simulate outside click to close
		act(() => {
			const mousedownEvent = new MouseEvent("mousedown", {
				bubbles: true,
				cancelable: true,
			});
			document.body.dispatchEvent(mousedownEvent);
		});

		// Wait for React to update the DOM and then check
		vi.useFakeTimers();
		vi.runAllTimers();
		vi.useRealTimers();
		expect(screen.queryByText(/profile/i)).not.toBeInTheDocument();
	});

	it("toggles theme when theme switch is clicked", async () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const themeSwitch = screen.getByRole("switch");
		await userEvent.click(themeSwitch);

		expect(mockToggleTheme).toHaveBeenCalledTimes(1);
	});

	it("shows dark theme state correctly", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		vi.mocked(ThemeContext.useTheme).mockReturnValue({
			theme: "dark",
			toggleTheme: mockToggleTheme,
		});

		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const themeSwitch = screen.getByRole("switch");
		expect(themeSwitch).toBeChecked();
	});

	it("shows light theme state correctly", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		vi.mocked(ThemeContext.useTheme).mockReturnValue({
			theme: "light",
			toggleTheme: mockToggleTheme,
		});

		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const themeSwitch = screen.getByRole("switch");
		expect(themeSwitch).not.toBeChecked();
	});

	it("calls logout when sign out is clicked", async () => {
		mockLogout.mockResolvedValue(undefined);
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));

		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		// Open the menu
		const menuBtn = screen.getByLabelText(/toggle user menu/i);
		await userEvent.click(menuBtn);

		// Click sign out
		const signOutLink = screen.getByText(/sign out/i);
		await userEvent.click(signOutLink);

		expect(mockLogout).toHaveBeenCalledTimes(1);
	});

	it("closes menu after logout", async () => {
		mockLogout.mockResolvedValue(undefined);
		vi.mocked(AuthContext.useAuth).mockReturnValue(createMockAuthContext(true));

		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		// Open the menu
		const menuBtn = screen.getByLabelText(/toggle user menu/i);
		await userEvent.click(menuBtn);

		// Check menu is open
		expect(screen.getByTestId("mobile-menu")).toBeInTheDocument();

		// Click sign out
		const signOutLink = screen.getByText(/sign out/i);
		await userEvent.click(signOutLink);

		// Wait for logout to complete and menu to close
		vi.useFakeTimers();
		vi.runAllTimers();
		vi.useRealTimers();
		expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
	});

	it("displays current year in copyright", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const currentYear = new Date().getFullYear();
		expect(screen.getByText(`© ${currentYear}`)).toBeInTheDocument();
	});

	it("shows contact email link", () => {
		vi.mocked(AuthContext.useAuth).mockReturnValue(
			createMockAuthContext(false),
		);
		render(
			<MemoryRouter>
				<Footer />
			</MemoryRouter>,
		);

		const contactLink = screen.getByText(/contact/i);
		expect(contactLink).toBeInTheDocument();
		expect(contactLink.closest("a")).toHaveAttribute(
			"href",
			expect.stringMatching(/^mailto:/),
		);
	});
});
