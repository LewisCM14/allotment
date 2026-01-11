import { render, screen, act } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import AppRoutes from "./AppRoutes";
import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";
import * as AuthContext from "@/store/auth/AuthContext";

// Mock all lazy-loaded components
vi.mock("../features/auth/forms/LoginForm", () => ({
	default: () => <div data-testid="login-form">Login Form</div>,
}));

vi.mock("../features/registration/forms/RegisterForm", () => ({
	default: () => <div data-testid="register-form">Register Form</div>,
}));

vi.mock("../features/auth/forms/ResetPassword", () => ({
	default: () => <div data-testid="reset-password">Reset Password</div>,
}));

vi.mock("../features/auth/forms/SetNewPassword", () => ({
	default: () => <div data-testid="set-new-password">Set New Password</div>,
}));

vi.mock("../features/user/pages/UserProfile", () => ({
	default: () => <div data-testid="user-profile">User Profile</div>,
}));

vi.mock("../features/todo/pages/Todo", () => ({
	default: () => <div>Home Page</div>,
}));

vi.mock("../features/family/pages/BotanicalGroups", () => ({
	default: () => <div data-testid="botanical-groups">Botanical Groups</div>,
}));

vi.mock("../features/family/pages/FamilyInfo", () => ({
	default: () => <div data-testid="family-info">Family Info</div>,
}));

vi.mock("../features/registration/pages/EmailVerification", () => ({
	default: () => <div data-testid="email-verification">Email Verification</div>,
}));

vi.mock("../features/allotment/pages/UserAllotmentInfo", () => ({
	default: () => <div data-testid="allotment-page">Allotment Page</div>,
}));

vi.mock("../components/NotFound", () => ({
	default: () => <div data-testid="not-found">Not Found</div>,
}));

vi.mock("@/store/auth/AuthContext");

const mockUseAuth = AuthContext.useAuth as unknown as Mock;

// Test helper components
function LocationTracker() {
	const location = useLocation();
	return <div data-testid="current-location">{location.pathname}</div>;
}

function TestPage({ name }: { name: string }) {
	return (
		<div data-testid={`page-${name.toLowerCase()}`}>
			<h1>{name} Page</h1>
		</div>
	);
}

// Test utilities
async function renderWithRouter(
	initialEntries: string[] = ["/"],
	isAuthenticated = false,
) {
	mockUseAuth.mockReturnValue({
		isAuthenticated,
		login: vi.fn(),
		logout: vi.fn(),
		user: isAuthenticated ? { user_id: "123", user_first_name: "Test" } : null,
	});

	const result = render(
		<MemoryRouter initialEntries={initialEntries}>
			<AppRoutes />
			<LocationTracker />
		</MemoryRouter>,
	);

	vi.useFakeTimers();
	await act(async () => {
		vi.runAllTimers();
	});
	vi.useRealTimers();

	return result;
}

function renderWithAuth(
	component: React.ReactElement,
	{
		isAuthenticated = false,
		initialPath = "/",
	}: { isAuthenticated?: boolean; initialPath?: string } = {},
) {
	mockUseAuth.mockReturnValue({
		isAuthenticated,
		user: isAuthenticated ? { user_id: "123", user_first_name: "Test" } : null,
	});

	return render(
		<MemoryRouter initialEntries={[initialPath]}>
			{component}
			<LocationTracker />
		</MemoryRouter>,
	);
}

describe("Application Routes", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe("Route Guards", () => {
		describe("ProtectedRoute", () => {
			it("renders children when user is authenticated", () => {
				renderWithAuth(
					<ProtectedRoute>
						<TestPage name="Protected" />
					</ProtectedRoute>,
					{ isAuthenticated: true },
				);

				expect(screen.getByTestId("page-protected")).toBeInTheDocument();
			});

			it("redirects when user is not authenticated", () => {
				renderWithAuth(
					<ProtectedRoute>
						<TestPage name="Protected" />
					</ProtectedRoute>,
					{ isAuthenticated: false },
				);

				expect(screen.queryByTestId("page-protected")).not.toBeInTheDocument();
			});
		});

		describe("PublicRoute", () => {
			it("renders children when user is not authenticated", () => {
				renderWithAuth(
					<PublicRoute>
						<TestPage name="Public" />
					</PublicRoute>,
					{ isAuthenticated: false },
				);

				expect(screen.getByTestId("page-public")).toBeInTheDocument();
			});

			it("redirects when user is authenticated", () => {
				renderWithAuth(
					<PublicRoute>
						<TestPage name="Public" />
					</PublicRoute>,
					{ isAuthenticated: true },
				);

				expect(screen.queryByTestId("page-public")).not.toBeInTheDocument();
			});
		});
	});

	describe("Public Routes (unauthenticated)", () => {
		it("renders login form at /login", async () => {
			await renderWithRouter(["/login"], false);
			expect(screen.getByTestId("login-form")).toBeInTheDocument();
		});

		it("renders register form at /register", async () => {
			await renderWithRouter(["/register"], false);
			expect(screen.getByTestId("register-form")).toBeInTheDocument();
		});

		it("renders reset password at /reset-password", async () => {
			await renderWithRouter(["/reset-password"], false);
			expect(screen.getByTestId("reset-password")).toBeInTheDocument();
		});

		it("redirects to login when accessing protected routes", async () => {
			await renderWithRouter(["/profile"], false);
			expect(screen.getByTestId("login-form")).toBeInTheDocument();
		});
	});

	describe("Protected Routes (authenticated)", () => {
		it("renders home page at /", async () => {
			await renderWithRouter(["/"], true);
			expect(screen.getByText("Home Page")).toBeInTheDocument();
		});

		it("renders user profile at /profile", async () => {
			await renderWithRouter(["/profile"], true);
			expect(screen.getByTestId("user-profile")).toBeInTheDocument();
		});

		it("renders botanical groups at /botanical_groups", async () => {
			await renderWithRouter(["/botanical_groups"], true);
			expect(screen.getByTestId("botanical-groups")).toBeInTheDocument();
		});

		it("renders family info at /family/:familyId", async () => {
			await renderWithRouter(["/family/123"], true);
			expect(screen.getByTestId("family-info")).toBeInTheDocument();
		});

		it("redirects to home when accessing public routes", async () => {
			await renderWithRouter(["/login"], true);
			expect(screen.getByText("Home Page")).toBeInTheDocument();
		});
	});

	describe("Special Routes", () => {
		it("renders email verification page", async () => {
			await renderWithRouter(["/verify-email"], false);
			expect(screen.getByTestId("email-verification")).toBeInTheDocument();
		});

		it("renders not found page for unknown routes", async () => {
			await renderWithRouter(["/unknown-route"], false);
			expect(screen.getByTestId("not-found")).toBeInTheDocument();
		});
	});

	describe("Route Protection Scenarios", () => {
		const protectedRoutes = [
			"/profile",
			"/allotment",
			"/botanical_groups",
			"/family/123",
		];
		const publicRoutes = ["/login", "/register", "/reset-password"];

		for (const route of protectedRoutes) {
			it(`${route} requires authentication`, () => {
				renderWithAuth(
					<ProtectedRoute>
						<TestPage name="Protected Content" />
					</ProtectedRoute>,
					{ isAuthenticated: false, initialPath: route },
				);

				expect(
					screen.queryByTestId("page-protected content"),
				).not.toBeInTheDocument();
			});
		}

		for (const route of publicRoutes) {
			it(`${route} is accessible without authentication`, () => {
				renderWithAuth(
					<PublicRoute>
						<TestPage name="Public Content" />
					</PublicRoute>,
					{ isAuthenticated: false, initialPath: route },
				);

				expect(screen.getByTestId("page-public content")).toBeInTheDocument();
			});
		}
	});
});
