import { render, screen, act, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Header from "./HeaderContainer";
import { HeaderPresenter } from "./HeaderPresenter";
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
		vi.useFakeTimers();
		vi.runAllTimers();
		vi.useRealTimers();
		expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
	});
});

describe("HeaderPresenter", () => {
	const navLinks = [
		{ href: "/grow-guides", label: "Grow Guides" },
		{ href: "/botanical_groups", label: "Families" },
		{ href: "/public-guides", label: "Public Guides" },
	];

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders app title from envConfig", () => {
		const original = globalThis.envConfig;
		globalThis.envConfig = {
			...globalThis.envConfig,
			VITE_APP_TITLE: "Test App",
		};
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		expect(screen.getByText("Test App")).toBeInTheDocument();
		globalThis.envConfig = original;
	});

	it("renders logo image with correct attributes", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		const logo = screen.getByAltText("Logo");
		expect(logo).toBeInTheDocument();
		expect(logo).toHaveAttribute("width", "32");
		expect(logo).toHaveAttribute("height", "32");
	});

	it("renders desktop nav links when authenticated", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		expect(screen.getByText("Grow Guides")).toBeInTheDocument();
		expect(screen.getByText("Families")).toBeInTheDocument();
		expect(screen.getByText("Public Guides")).toBeInTheDocument();
	});

	it("renders login link when not authenticated", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={[]}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={false}
			/>,
		);
		expect(screen.getByText("Login")).toBeInTheDocument();
	});

	it("does not show menu button when not authenticated", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={[]}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={false}
			/>,
		);
		expect(
			screen.queryByLabelText(/toggle navigation menu/i),
		).not.toBeInTheDocument();
	});

	it("shows menu button when authenticated", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		expect(
			screen.getByLabelText(/toggle navigation menu/i),
		).toBeInTheDocument();
	});

	it("calls onMenuClick when menu button is clicked", async () => {
		const onMenuClick = vi.fn();
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={onMenuClick}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		await userEvent.click(screen.getByLabelText(/toggle navigation menu/i));
		expect(onMenuClick).toHaveBeenCalledTimes(1);
	});

	it("renders mobile menu when isOpen is true and authenticated", () => {
		render(
			<HeaderPresenter
				isOpen={true}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		expect(screen.getByTestId("mobile-menu")).toBeInTheDocument();
		// Mobile menu should show all nav links
		const mobileMenu = screen.getByTestId("mobile-menu");
		expect(mobileMenu).toHaveTextContent("Grow Guides");
		expect(mobileMenu).toHaveTextContent("Families");
		expect(mobileMenu).toHaveTextContent("Public Guides");
	});

	it("does not render mobile menu when isOpen is false", () => {
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
			/>,
		);
		expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
	});

	it("does not render mobile menu when not authenticated even if isOpen", () => {
		render(
			<HeaderPresenter
				isOpen={true}
				navLinks={[]}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={false}
			/>,
		);
		expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
	});

	it("calls closeMenu when a mobile menu link is clicked", async () => {
		const closeMenu = vi.fn();
		render(
			<HeaderPresenter
				isOpen={true}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={closeMenu}
				isAuthenticated={true}
			/>,
		);
		const mobileMenu = screen.getByTestId("mobile-menu");
		const link = mobileMenu.querySelector('a[href="/grow-guides"]');
		expect(link).not.toBeNull();
		fireEvent.click(link as Element);
		expect(closeMenu).toHaveBeenCalledTimes(1);
	});

	it("calls onLinkHover when desktop link is hovered", async () => {
		const onLinkHover = vi.fn();
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
				onLinkHover={onLinkHover}
			/>,
		);
		fireEvent.mouseEnter(screen.getByText("Grow Guides"));
		expect(onLinkHover).toHaveBeenCalledWith("/grow-guides");
	});

	it("calls onLinkHover on login link hover when not authenticated", async () => {
		const onLinkHover = vi.fn();
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={[]}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={false}
				onLinkHover={onLinkHover}
			/>,
		);
		fireEvent.mouseEnter(screen.getByText("Login"));
		expect(onLinkHover).toHaveBeenCalledWith("/login");
	});

	it("calls onLinkHover on focus of desktop link", async () => {
		const onLinkHover = vi.fn();
		render(
			<HeaderPresenter
				isOpen={false}
				navLinks={navLinks}
				onMenuClick={vi.fn()}
				closeMenu={vi.fn()}
				isAuthenticated={true}
				onLinkHover={onLinkHover}
			/>,
		);
		fireEvent.focus(screen.getByText("Families"));
		expect(onLinkHover).toHaveBeenCalledWith("/botanical_groups");
	});
});
