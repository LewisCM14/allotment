import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AllotmentPage from "./UserAllotmentInfo";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithReactQuery } from "@/test-utils";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { buildUrl } from "@/mocks/buildUrl";
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

function renderPage() {
	const result = renderWithReactQuery(<AllotmentPage />);
	return result;
}

describe("AllotmentPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: true });
	});

	it("renders loading state initially", async () => {
		// Set up MSW handler that never resolves
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return new Promise(() => {}); // Never resolves - simulates loading
			}),
		);

		renderPage();
		expect(screen.getByLabelText(/loading allotment data/i)).toBeInTheDocument();
	});

	it("renders form for new user (no existing allotment)", async () => {
		// Set up MSW handler to return 404 for getUserAllotment
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return new HttpResponse(
					JSON.stringify({ detail: "No allotment found" }),
					{ status: 404 },
				);
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);
		// For new users, it should start in edit mode automatically
		expect(screen.getByLabelText(/postal\/zip code/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/width/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/length/i)).toBeInTheDocument();
		expect(screen.getByText(/total area/i)).toBeInTheDocument();
	});

	it("renders form with existing allotment data", async () => {
		// Set up MSW handler to return existing allotment data
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return HttpResponse.json({
					allotment_postal_zip_code: "A1A 1A1",
					allotment_width_meters: 10,
					allotment_length_meters: 20,
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);

		// For existing users, it should start in read-only mode
		expect(screen.getByText("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByText("10 m")).toBeInTheDocument();
		expect(screen.getByText("20 m")).toBeInTheDocument();
		expect(screen.getByText(/200\.0 m²/)).toBeInTheDocument();

		// Should have an edit button
		expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
	});

	it("submits form to create new allotment", async () => {
		// Set up MSW handlers for the test flow
		server.use(
			// First call to get allotment returns 404 (new user)
			http.get(buildUrl("/users/allotment"), () => {
				return new HttpResponse(
					JSON.stringify({ detail: "No allotment found" }),
					{ status: 404 },
				);
			}),
			// POST to create allotment succeeds
			http.post(buildUrl("/users/allotment"), () => {
				return HttpResponse.json({
					allotment_postal_zip_code: "B2B 2B2",
					allotment_width_meters: 5,
					allotment_length_meters: 6,
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);

		// New users start in edit mode, so form fields should be available
		await userEvent.type(screen.getByLabelText(/postal\/zip code/i), "B2B 2B2");
		await userEvent.clear(screen.getByLabelText(/width/i));
		await userEvent.type(screen.getByLabelText(/width/i), "5");
		await userEvent.clear(screen.getByLabelText(/length/i));
		await userEvent.type(screen.getByLabelText(/length/i), "6");
		await userEvent.click(screen.getByRole("button", { name: /save/i }));

		// Verify the form submission completed
		await waitFor(
			() => {
				expect(screen.queryByText(/saving/i)).not.toBeInTheDocument();
			},
			{ container },
		);
	});

	it("shows validation errors for empty fields", async () => {
		// Set up MSW handler to return 404 for getUserAllotment (new user scenario)
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return new HttpResponse(
					JSON.stringify({ detail: "No allotment found" }),
					{ status: 404 },
				);
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);

		// Clear the fields and try to submit
		const postalField = screen.getByLabelText(/postal\/zip code/i);
		const widthField = screen.getByLabelText(/width/i);
		const lengthField = screen.getByLabelText(/length/i);

		await userEvent.clear(postalField);
		await userEvent.clear(widthField);
		await userEvent.clear(lengthField);

		// Try to save with empty fields
		await userEvent.click(screen.getByRole("button", { name: /save/i }));

		// Should show validation errors
		expect(await screen.findByText(/width is required/i)).toBeInTheDocument();
	});

	it("allows editing existing allotment data", async () => {
		// Set up MSW handlers for existing user flow
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return HttpResponse.json({
					allotment_postal_zip_code: "A1A 1A1",
					allotment_width_meters: 10,
					allotment_length_meters: 20,
				});
			}),
			http.put(buildUrl("/users/allotment"), () => {
				return HttpResponse.json({
					allotment_postal_zip_code: "B2B 2B2",
					allotment_width_meters: 15,
					allotment_length_meters: 25,
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);

		// Should show read-only data initially
		expect(screen.getByText("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByText("10 m")).toBeInTheDocument();
		expect(screen.getByText("20 m")).toBeInTheDocument();

		// Click edit button
		await userEvent.click(screen.getByRole("button", { name: /edit/i }));

		// Now should show form fields
		expect(screen.getByDisplayValue("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByDisplayValue("10")).toBeInTheDocument();
		expect(screen.getByDisplayValue("20")).toBeInTheDocument();

		// Edit the values
		const postalField = screen.getByLabelText(/postal\/zip code/i);
		const widthField = screen.getByLabelText(/width/i);
		const lengthField = screen.getByLabelText(/length/i);

		await userEvent.clear(postalField);
		await userEvent.type(postalField, "B2B 2B2");
		await userEvent.clear(widthField);
		await userEvent.type(widthField, "15");
		await userEvent.clear(lengthField);
		await userEvent.type(lengthField, "25");

		// Save changes
		await userEvent.click(screen.getByRole("button", { name: /save/i }));

		// Should complete successfully
		await waitFor(
			() => {
				expect(screen.queryByText(/saving/i)).not.toBeInTheDocument();
			},
			{ container },
		);
	});

	it("allows canceling edits", async () => {
		// Set up MSW handler for existing user
		server.use(
			http.get(buildUrl("/users/allotment"), () => {
				return HttpResponse.json({
					allotment_postal_zip_code: "A1A 1A1",
					allotment_width_meters: 10,
					allotment_length_meters: 20,
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Your Allotment")).toBeInTheDocument(),
			{ container },
		);

		// Click edit button
		await userEvent.click(screen.getByRole("button", { name: /edit/i }));

		// Make some changes
		const postalField = screen.getByLabelText(/postal\/zip code/i);
		await userEvent.clear(postalField);
		await userEvent.type(postalField, "CHANGED");

		// Cancel the changes
		await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

		// Should be back in read-only mode with original data
		expect(screen.getByText("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByText("10 m")).toBeInTheDocument();
		expect(screen.getByText("20 m")).toBeInTheDocument();
	});

	it("redirects to login if not authenticated", async () => {
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: false });
		const { container } = renderPage();
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"), {
			container,
		});
	});
});
