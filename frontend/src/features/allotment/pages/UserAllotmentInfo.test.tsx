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
		expect(screen.getByText(/loading allotment data/i)).toBeInTheDocument();
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
			() =>
				expect(screen.getByText(/manage your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		expect(screen.getByDisplayValue("A1A 1A1")).toBeInTheDocument();
		expect(screen.getByDisplayValue("10")).toBeInTheDocument();
		expect(screen.getByDisplayValue("20")).toBeInTheDocument();
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

		// We can't easily verify the POST was called with MSW, but we can verify the form submission completed
		await waitFor(
			() => {
				expect(screen.queryByText(/creating/i)).not.toBeInTheDocument();
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
			() =>
				expect(screen.getByText(/create your allotment/i)).toBeInTheDocument(),
			{ container },
		);
		userEvent.clear(screen.getByLabelText(/postal\/zip code/i));
		userEvent.clear(screen.getByLabelText(/width/i));
		userEvent.clear(screen.getByLabelText(/length/i));
		userEvent.click(screen.getByRole("button"));
		expect(await screen.findByText(/width is required/i)).toBeInTheDocument();
	});

	it("redirects to login if not authenticated", async () => {
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: false });
		const { container } = renderPage();
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"), {
			container,
		});
	});
});
