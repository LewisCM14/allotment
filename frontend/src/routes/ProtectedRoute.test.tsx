import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import ProtectedRoute from "./ProtectedRoute";
import * as AuthContext from "@/store/auth/AuthContext";

vi.mock("@/store/auth/AuthContext");

const mockUseAuth = AuthContext.useAuth as unknown as Mock;

function renderProtectedRoute(
	isAuthenticated = false,
	initialEntries = ["/protected"],
) {
	mockUseAuth.mockReturnValue({
		isAuthenticated,
	});

	return render(
		<MemoryRouter initialEntries={initialEntries}>
			<ProtectedRoute>
				<div data-testid="protected-content">Protected Content</div>
			</ProtectedRoute>
		</MemoryRouter>,
	);
}

describe("ProtectedRoute", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders children when user is authenticated", () => {
		renderProtectedRoute(true);
		expect(screen.getByTestId("protected-content")).toBeInTheDocument();
	});

	it("redirects to login when user is not authenticated", () => {
		renderProtectedRoute(false);
		expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument();
	});

	it("calls useAuth hook", () => {
		renderProtectedRoute(true);
		expect(mockUseAuth).toHaveBeenCalled();
	});
});
