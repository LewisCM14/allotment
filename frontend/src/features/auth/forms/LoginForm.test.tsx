import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginForm from "./LoginForm";
import * as AuthContext from "@/store/auth/AuthContext";
import * as AuthService from "../services/AuthService";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock useAuth
vi.mock("@/store/auth/AuthContext");
// Mock AuthService
vi.mock("../services/AuthService");

function renderForm() {
	// Explicitly return the result of render, including container
	return render(
		<MemoryRouter>
			<LoginForm />
		</MemoryRouter>,
	);
}

describe("LoginForm", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(AuthContext.useAuth as unknown as Mock).mockReturnValue({
			login: vi.fn(),
		});
		// Default to online
		Object.defineProperty(window.navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});

	it("renders all fields and submit button", () => {
		renderForm();
		expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
		// Specify selector to avoid matching the toggle button
		expect(
			screen.getByLabelText(/password/i, { selector: "input" }),
		).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
	});

	it("shows validation errors for empty fields", async () => {
		renderForm();
		await userEvent.click(screen.getByRole("button", { name: /login/i }));
		expect(await screen.findAllByText(/required/i)).not.toHaveLength(0);
	});

	it("calls loginUser and login on successful submit", async () => {
		const loginMock = vi.fn();
		(AuthContext.useAuth as unknown as Mock).mockReturnValue({
			login: loginMock,
		});
		(AuthService.loginUser as unknown as Mock).mockResolvedValue({
			tokens: { access_token: "token", refresh_token: "refresh" },
			firstName: "Test",
			userData: {
				user_id: "id",
				user_email: "test@example.com",
				is_email_verified: true,
			},
		});
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
		await userEvent.type(
			screen.getByLabelText(/password/i, { selector: "input" }),
			"password123",
		);
		await userEvent.click(screen.getByRole("button", { name: /login/i }));
		// Instead of waitFor on the mock, check for a post-login UI change if possible
		// If no UI change, just assert the mocks synchronously
		expect(AuthService.loginUser).toHaveBeenCalledWith(
			"test@example.com",
			"password123",
		);
		expect(loginMock).toHaveBeenCalled();
	});

	it("shows error on login failure", async () => {
		(AuthService.loginUser as unknown as Mock).mockRejectedValue(
			new Error("Invalid credentials"),
		);
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "fail@example.com");
		await userEvent.type(
			screen.getByLabelText(/password/i, { selector: "input" }),
			"wrong",
		);
		await userEvent.click(screen.getByRole("button", { name: /login/i }));
		expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
	});

	it("toggles password visibility", async () => {
		renderForm();
		const passwordInput = screen.getByLabelText(/password/i, {
			selector: "input",
		});
		const toggleBtn = screen.getByRole("button", { name: /show password/i });
		expect(passwordInput).toHaveAttribute("type", "password");
		await userEvent.click(toggleBtn);
		expect(passwordInput).toHaveAttribute("type", "text");
		await userEvent.click(toggleBtn);
		expect(passwordInput).toHaveAttribute("type", "password");
	});
});
