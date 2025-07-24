import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import PublicRoute from "./PublicRoute";
import * as AuthContext from "@/store/auth/AuthContext";

vi.mock("@/store/auth/AuthContext");

const mockUseAuth = AuthContext.useAuth as unknown as Mock;

function renderPublicRoute(
	isAuthenticated = false,
	initialEntries = ["/login"],
) {
	mockUseAuth.mockReturnValue({
		isAuthenticated,
	});

	return render(
		<MemoryRouter initialEntries={initialEntries}>
			<PublicRoute>
				<div data-testid="public-content">Public Content</div>
			</PublicRoute>
		</MemoryRouter>,
	);
}

describe("PublicRoute", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders children when user is not authenticated", () => {
		renderPublicRoute(false);
		expect(screen.getByTestId("public-content")).toBeInTheDocument();
	});

	it("redirects to home when user is authenticated", () => {
		renderPublicRoute(true);
		expect(screen.queryByTestId("public-content")).not.toBeInTheDocument();
		// Similar to ProtectedRoute, we verify children don't render
	});

	it("calls useAuth hook", () => {
		renderPublicRoute(false);
		expect(mockUseAuth).toHaveBeenCalled();
	});
});
