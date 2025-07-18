import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AllotmentPage from "./AllotmentPage";
import * as UserService from "../services/UserService";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithRouter } from "@/test-utils";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";

// Mock useAuth
vi.mock("@/store/auth/AuthContext", () => ({
	useAuth: vi.fn(),
}));

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
	};
});

// Mock UserService
vi.mock("../services/UserService");

function renderPage() {
	const result = renderWithRouter(<AllotmentPage />);
	return result;
}

describe("AllotmentPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: true });
	});

	it("renders loading state initially", async () => {
		(UserService.getUserAllotment as unknown as Mock).mockImplementation(
			() => new Promise(() => {}),
		);
		renderPage();
		expect(screen.getByText(/loading allotment data/i)).toBeInTheDocument();
	});

	it("renders form for new user (no existing allotment)", async () => {
		(UserService.getUserAllotment as unknown as Mock).mockRejectedValueOnce(
			new Error("No allotment"),
		);
		const { container } = renderPage();
		await waitFor(
			() =>
				expect(screen.getByText(/create your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		expect(screen.getByLabelText(/postal\/zip code/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/width/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/length/i)).toBeInTheDocument();
		expect(screen.getByText(/total area/i)).toBeInTheDocument();
	});

	it("renders form with existing allotment data", async () => {
		(UserService.getUserAllotment as unknown as Mock).mockResolvedValueOnce({
			allotment_postal_zip_code: "A1A 1A1",
			allotment_width_meters: 10,
			allotment_length_meters: 20,
		});
		const { container } = renderPage();
		await waitFor(
			() =>
				expect(screen.getByText(/manage your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		expect(screen.getByDisplayValue("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByDisplayValue("10")).toBeInTheDocument();
		expect(screen.getByDisplayValue("20")).toBeInTheDocument();
	});

	it("submits form to create new allotment", async () => {
		(UserService.getUserAllotment as unknown as Mock).mockRejectedValueOnce(
			new Error("No allotment"),
		);
		(UserService.createUserAllotment as unknown as Mock).mockResolvedValueOnce({
			allotment_postal_zip_code: "B2B 2B2",
			allotment_width_meters: 5,
			allotment_length_meters: 6,
		});
		const { container } = renderPage();
		await waitFor(
			() =>
				expect(screen.getByText(/create your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		await userEvent.type(screen.getByLabelText(/postal\/zip code/i), "B2B 2B2");
		await userEvent.clear(screen.getByLabelText(/width/i));
		await userEvent.type(screen.getByLabelText(/width/i), "5");
		await userEvent.clear(screen.getByLabelText(/length/i));
		await userEvent.type(screen.getByLabelText(/length/i), "6");
		await userEvent.click(
			screen.getByRole("button", { name: /create allotment/i }),
		);
		await waitFor(
			() =>
				expect(
					(UserService.createUserAllotment as unknown as Mock).mock.calls
						.length,
				).toBeGreaterThan(0),
			{ container },
		);
	});

	it("shows validation errors for empty fields", async () => {
		(UserService.getUserAllotment as unknown as Mock).mockRejectedValueOnce(
			new Error("No allotment"),
		);
		const { container } = renderPage();
		await waitFor(
			() =>
				expect(screen.getByText(/create your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		userEvent.clear(screen.getByLabelText(/postal\/zip code/i));
		userEvent.clear(screen.getByLabelText(/width/i));
		userEvent.clear(screen.getByLabelText(/length/i));
		userEvent.click(screen.getByRole("button"));
		expect(
			await screen.findByText(/width must be at least 1 meter/i),
		).toBeInTheDocument();
	});

	it("shows offline message and disables submit", async () => {
		// Mock navigator.onLine as false before rendering
		const originalOnLine = navigator.onLine;
		Object.defineProperty(navigator, "onLine", {
			value: false,
			configurable: true,
		});

		(UserService.getUserAllotment as unknown as Mock).mockRejectedValueOnce(
			new Error("No allotment"),
		);
		const { container } = renderPage();
		await waitFor(
			() =>
				expect(
					screen.getByText(/you are currently offline/i),
				).toBeInTheDocument(),
			{ container },
		);
		expect(screen.getByRole("button")).toBeDisabled();

		// Restore original value
		Object.defineProperty(navigator, "onLine", {
			value: originalOnLine,
			configurable: true,
		});
	});

	it("redirects to login if not authenticated", async () => {
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: false });
		const { container } = renderPage();
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"), {
			container,
		});
	});
});
