import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EmailVerificationPage from "./EmailVerification";
import * as UserService from "../services/UserService";
import { renderWithRouter } from "@/test-utils";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { useNavigate, useSearchParams } from "react-router-dom";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
	const actual =
		await vi.importActual<typeof import("react-router-dom")>(
			"react-router-dom",
		);
	return {
		...actual,
		useNavigate: () => mockNavigate,
		useSearchParams: vi.fn(),
	};
});

// Mock UserService
vi.mock("../services/UserService");

function setupSearchParams(params: Record<string, string | undefined>) {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined) searchParams.set(key, value);
	}
	(useSearchParams as unknown as Mock).mockReturnValue([searchParams]);
}

function renderPage() {
	return renderWithRouter(<EmailVerificationPage />);
}

describe("EmailVerificationPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("shows error if no token is provided", async () => {
		setupSearchParams({});
		const { container } = renderPage();
		await waitFor(
			() => {
				expect(
					screen.getByText(/no verification token provided/i),
				).toBeInTheDocument();
			},
			{ container },
		);
	});

	it("shows success message on valid token", async () => {
		setupSearchParams({ token: "valid-token" });
		(UserService.verifyEmail as unknown as Mock).mockResolvedValueOnce({
			message: "Email verified",
		});
		const { container } = renderPage();
		await waitFor(
			() => {
				expect(screen.getByText(/email verified!/i)).toBeInTheDocument();
			},
			{ container },
		);
	});

	it("shows password reset flow if fromReset param is true", async () => {
		setupSearchParams({ token: "valid-token", fromReset: "true" });
		(UserService.verifyEmail as unknown as Mock).mockResolvedValueOnce({
			message: "Email verified",
		});
		const { container } = renderPage();
		await waitFor(
			() => {
				expect(
					screen.getByText(/now you can proceed to reset your password/i),
				).toBeInTheDocument();
			},
			{ container },
		);
		await userEvent.click(
			screen.getByRole("button", { name: /reset password/i }),
		);
		await waitFor(
			() => {
				expect(mockNavigate).toHaveBeenCalledWith("/reset-password");
			},
			{ container },
		);
	});

	it("shows error message on verification failure", async () => {
		setupSearchParams({ token: "invalid-token" });
		(UserService.verifyEmail as unknown as Mock).mockRejectedValueOnce(
			new Error("Invalid or expired token"),
		);
		const { container } = renderPage();
		await waitFor(
			() => {
				expect(screen.getByText(/verification failed/i)).toBeInTheDocument();
				expect(
					screen.getByText(/invalid or expired token/i),
				).toBeInTheDocument();
			},
			{ container },
		);
	});

	it("shows request new verification link and return to home links on error", async () => {
		setupSearchParams({ token: "invalid-token" });
		(UserService.verifyEmail as unknown as Mock).mockRejectedValueOnce(
			new Error("Invalid or expired token"),
		);
		const { container } = renderPage();
		await waitFor(
			() => {
				expect(
					screen.getByRole("link", { name: /request new verification link/i }),
				).toBeInTheDocument();
				expect(
					screen.getByRole("link", { name: /return to home/i }),
				).toBeInTheDocument();
			},
			{ container },
		);
	});
});
