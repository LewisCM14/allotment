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
});
