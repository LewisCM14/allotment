import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResetPassword from "./ResetPassword";
import * as AuthService from "../services/AuthService";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock AuthService
vi.mock("../services/AuthService");

describe("ResetPassword", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		Object.defineProperty(window.navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});

	function renderForm() {
		return render(
			<MemoryRouter>
				<ResetPassword />
			</MemoryRouter>,
		);
	}

	it("renders email field and submit button", () => {
		renderForm();
		expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /send reset link/i }),
		).toBeInTheDocument();
	});

	it("shows validation error for empty email", async () => {
		renderForm();
		await userEvent.click(
			screen.getByRole("button", { name: /send reset link/i }),
		);
		// The form shows a specific message for invalid/empty email
		expect(await screen.findByText(/valid email address/i)).toBeInTheDocument();
	});

	it("calls requestPasswordReset and shows success message", async () => {
		(AuthService.requestPasswordReset as unknown as Mock).mockResolvedValue(
			undefined,
		);
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
		await userEvent.click(
			screen.getByRole("button", { name: /send reset link/i }),
		);
		expect(AuthService.requestPasswordReset).toHaveBeenCalledWith(
			"test@example.com",
		);
		// Wait for the success message to appear
		expect(
			await screen.findByText(/if your email exists/i),
		).toBeInTheDocument();
	});

	it("shows error if request fails", async () => {
		(AuthService.requestPasswordReset as unknown as Mock).mockRejectedValue(
			new Error("Email not verified"),
		);
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "fail@example.com");
		await userEvent.click(
			screen.getByRole("button", { name: /send reset link/i }),
		);
		expect(await screen.findByText(/not verified/i)).toBeInTheDocument();
	});

	it("shows generic error for non-Error exceptions", async () => {
		(AuthService.requestPasswordReset as unknown as Mock).mockRejectedValue(
			"string error",
		);
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
		await userEvent.click(
			screen.getByRole("button", { name: /send reset link/i }),
		);
		expect(await screen.findByText(/unexpected error/i)).toBeInTheDocument();
	});

	it("shows generic error for non-verification Error messages", async () => {
		(AuthService.requestPasswordReset as unknown as Mock).mockRejectedValue(
			new Error("Some other error"),
		);
		renderForm();
		await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
		await userEvent.click(
			screen.getByRole("button", { name: /send reset link/i }),
		);
		expect(
			await screen.findByText(/password reset failed/i),
		).toBeInTheDocument();
	});

	it("shows offline banner text when navigator is offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});
		expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
	});

	it("disables submit button when offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});
		expect(
			screen.getByRole("button", { name: /send reset link/i }),
		).toBeDisabled();
	});
});
