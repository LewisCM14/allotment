import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UserProfile from "./UserProfile";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithReactQuery } from "@/test-utils";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";

// Mock useAuth
vi.mock("@/store/auth/AuthContext", () => ({
	useAuth: vi.fn(),
}));

function renderPage() {
	return renderWithReactQuery(<UserProfile />);
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

	it("shows email not verified warning for unverified users", async () => {
		renderPage();
		expect(screen.getByText(/email not verified/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", {
				name: /send verification email/i,
			}),
		).toBeInTheDocument();
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

		renderPage();
		expect(screen.getByText(/✓ email verified/i)).toBeInTheDocument();
	});

	it("shows refresh button when user is verified", async () => {
		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: true,
			},
			firstName: "Testy",
		});

		renderPage();

		// Wait for the query to finish loading, then check for the refresh button
		await waitFor(
			() => {
				expect(
					screen.getByRole("button", { name: /refresh status/i }),
				).toBeInTheDocument();
			},
			{ timeout: 3000 },
		);
	});

	it("can interact with buttons without errors", async () => {
		// Mock endpoints
		server.use(
			http.post("http://localhost:8000/api/v1/request-verification", () => {
				return HttpResponse.json({
					message: "Verification email sent successfully",
				});
			}),
			http.get("http://localhost:8000/api/v1/check-email-verification", () => {
				return HttpResponse.json({ is_email_verified: true });
			}),
		);

		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: false,
			},
			firstName: "Testy",
		});

		renderPage();

		// Test send verification email button
		const verificationButton = screen.getByRole("button", {
			name: /send verification email/i,
		});
		expect(verificationButton).toBeInTheDocument();
		await userEvent.click(verificationButton);

		// Test refresh button - just check if we can find and click it without erroring
		const refreshButton = screen.getByRole("button", {
			name: /refresh status/i,
		});
		expect(refreshButton).toBeInTheDocument();
		await userEvent.click(refreshButton);

		// No specific assertions needed - just that no errors occurred
		expect(true).toBe(true);
	});
});
