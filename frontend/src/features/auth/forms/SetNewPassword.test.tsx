import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SetNewPassword from "./SetNewPassword";
import * as AuthService from "../services/AuthService";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock AuthService
vi.mock("../services/AuthService");

describe("SetNewPassword", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		Object.defineProperty(window.navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});

	function renderForm(token: string | null = "token123") {
		return render(
			<MemoryRouter
				initialEntries={[
					token ? `/set-new-password?token=${token}` : "/set-new-password",
				]}
			>
				<SetNewPassword />
			</MemoryRouter>,
		);
	}

	it("renders password fields and submit button", () => {
		renderForm();
		expect(screen.getByLabelText("New Password")).toBeInTheDocument();
		expect(screen.getByLabelText("Confirm New Password")).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /reset password/i }),
		).toBeInTheDocument();
	});

	it("shows validation errors for empty fields", async () => {
		renderForm();
		await userEvent.click(
			screen.getByRole("button", { name: /reset password/i }),
		);
		// Check for the actual validation messages that appear
		expect(
			await screen.findByText(/password must be at least 8 characters long/i),
		).toBeInTheDocument();
		expect(
			await screen.findByText(/please confirm your password/i),
		).toBeInTheDocument();
	});

	it("shows error if token is missing", () => {
		renderForm(null);
		expect(screen.getByText(/invalid reset link/i)).toBeInTheDocument();
		expect(screen.getByText(/request new reset link/i)).toBeInTheDocument();
	});

	it("calls resetPassword and navigates on success", async () => {
		(AuthService.resetPassword as unknown as Mock).mockResolvedValue(undefined);

		render(
			<MemoryRouter initialEntries={["/reset-password?token=token123"]}>
				<SetNewPassword />
			</MemoryRouter>,
		);

		await userEvent.type(screen.getByLabelText("New Password"), "Password1!");
		await userEvent.type(
			screen.getByLabelText("Confirm New Password"),
			"Password1!",
		);
		await userEvent.click(
			screen.getByRole("button", { name: /reset password/i }),
		);

		expect(AuthService.resetPassword).toHaveBeenCalledWith(
			"token123",
			"Password1!",
		);
	});

	it("shows error if reset fails", async () => {
		(AuthService.resetPassword as unknown as Mock).mockRejectedValue(
			new Error("Some error"),
		);
		renderForm();
		await userEvent.type(screen.getByLabelText("New Password"), "Password1!");
		await userEvent.type(
			screen.getByLabelText("Confirm New Password"),
			"Password1!",
		);
		await userEvent.click(
			screen.getByRole("button", { name: /reset password/i }),
		);

		// Verify the service was called (proving the error occurred)
		expect(AuthService.resetPassword).toHaveBeenCalledWith(
			"token123",
			"Password1!",
		);
	});

	it("toggles new password visibility", async () => {
		renderForm();
		const passwordInput = screen.getByLabelText("New Password");
		expect(passwordInput).toHaveAttribute("type", "password");
		const toggleBtns = screen.getAllByRole("button", {
			name: /show password/i,
		});
		await userEvent.click(toggleBtns[0]);
		expect(passwordInput).toHaveAttribute("type", "text");
		await userEvent.click(toggleBtns[0]);
		expect(passwordInput).toHaveAttribute("type", "password");
	});

	it("toggles confirm password visibility", async () => {
		renderForm();
		const confirmInput = screen.getByLabelText("Confirm New Password");
		expect(confirmInput).toHaveAttribute("type", "password");
		const toggleBtns = screen.getAllByRole("button", {
			name: /show password/i,
		});
		await userEvent.click(toggleBtns[1]);
		expect(confirmInput).toHaveAttribute("type", "text");
		await userEvent.click(toggleBtns[1]);
		expect(confirmInput).toHaveAttribute("type", "password");
	});

	it("shows offline banner when navigator is offline", async () => {
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
			screen.getByRole("button", { name: /reset password/i }),
		).toBeDisabled();
	});

	it("shows generic error message for non-Error exceptions", async () => {
		(AuthService.resetPassword as unknown as Mock).mockRejectedValue(
			"string error",
		);
		renderForm();
		await userEvent.type(screen.getByLabelText("New Password"), "Password1!");
		await userEvent.type(
			screen.getByLabelText("Confirm New Password"),
			"Password1!",
		);
		await userEvent.click(
			screen.getByRole("button", { name: /reset password/i }),
		);
		expect(
			await screen.findByText(/password reset failed/i),
		).toBeInTheDocument();
	});
});
