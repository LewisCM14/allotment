import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UserProfile from "./UserProfile";
import * as UserService from "../services/UserService";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithRouter } from "@/test-utils";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";

// Mock useAuth
vi.mock("@/store/auth/AuthContext", () => ({
	useAuth: vi.fn(),
}));

// Mock UserService
vi.mock("../services/UserService");

function renderPage() {
	return renderWithRouter(<UserProfile />);
}

describe("UserProfile", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: false,
			},
			firstName: "Testy",
		});
		localStorage.clear();
	});

	it("renders user name and email", () => {
		renderPage();
		expect(screen.getByText(/profile/i)).toBeInTheDocument();
		expect(screen.getByText(/testy/i)).toBeInTheDocument();
		expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
	});

	it("shows email not verified warning and allows sending verification email", async () => {
		(
			UserService.checkEmailVerificationStatus as unknown as Mock
		).mockResolvedValueOnce({ is_email_verified: false });
		(
			UserService.requestVerificationEmail as unknown as Mock
		).mockResolvedValueOnce({});
		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText(/email not verified/i)).toBeInTheDocument(),
			{ container },
		);
		const button = screen.getByRole("button", {
			name: /send verification email/i,
		});
		expect(button).toBeInTheDocument();
		await userEvent.click(button);
		await waitFor(
			() =>
				expect(UserService.requestVerificationEmail).toHaveBeenCalledWith(
					"test@example.com",
				),
			{ container },
		);
	});

	it("shows verified message if email is verified", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: true,
			},
			firstName: "Testy",
		});
		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText(/email verified/i)).toBeInTheDocument(),
			{ container },
		);
	});

	it("refreshes verification status when refresh button is clicked", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: true,
			},
			firstName: "Testy",
		});
		(
			UserService.checkEmailVerificationStatus as unknown as Mock
		).mockResolvedValueOnce({ is_email_verified: true });
		const { container } = renderPage();
		const refreshBtn = screen.getByRole("button", { name: /refresh status/i });
		await userEvent.click(refreshBtn);
		await waitFor(
			() =>
				expect(UserService.checkEmailVerificationStatus).toHaveBeenCalledWith(
					"test@example.com",
				),
			{ container },
		);
	});

	it("shows error if checkEmailVerificationStatus fails", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: true,
			},
			firstName: "Testy",
		});
		(
			UserService.checkEmailVerificationStatus as unknown as Mock
		).mockRejectedValueOnce(new Error("Network error"));
		const { container } = renderPage();
		const refreshBtn = screen.getByRole("button", { name: /refresh status/i });
		await userEvent.click(refreshBtn);
		await waitFor(
			() => expect(screen.getByText(/network error/i)).toBeInTheDocument(),
			{ container },
		);
	});

	it("shows error if requestVerificationEmail fails", async () => {
		(
			UserService.requestVerificationEmail as unknown as Mock
		).mockRejectedValueOnce(new Error("Send failed"));
		const { container } = renderPage();
		const button = screen.getByRole("button", {
			name: /send verification email/i,
		});
		await userEvent.click(button);
		await waitFor(
			() => expect(screen.getByText(/send failed/i)).toBeInTheDocument(),
			{ container },
		);
	});

	it("disables refresh button while checking status", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: true,
			},
			firstName: "Testy",
		});
		type ResolveType = (v: { is_email_verified: boolean }) => void;
		let resolve: ResolveType | undefined;
		(
			UserService.checkEmailVerificationStatus as unknown as Mock
		).mockImplementation(
			() =>
				new Promise<{ is_email_verified: boolean }>((r) => {
					resolve = r;
				}),
		);
		const { container } = renderPage();
		const refreshBtn = screen.getByRole("button", { name: /refresh status/i });
		await userEvent.click(refreshBtn);
		expect(refreshBtn).toBeDisabled();
		if (resolve) {
			resolve({ is_email_verified: false });
		}
	});

	it("shows error if user email is missing when requesting verification", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: null,
			firstName: null,
		});
		const { container } = renderPage();
		const button = screen.getByRole("button", {
			name: /send verification email/i,
		});
		await userEvent.click(button);
		await waitFor(
			() =>
				expect(
					screen.getByText(/user email not available/i),
				).toBeInTheDocument(),
			{ container },
		);
	});
});
