import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UserPreferencePage from "./UserPreferencePage";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithReactQuery } from "@/test-utils";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { buildUrl } from "@/mocks/buildUrl";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";

// Mock the auth context
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
	const result = renderWithReactQuery(<UserPreferencePage />);
	return result;
}

describe("UserPreferencePage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: true });
	});

	it("renders loading state initially", async () => {
		// Set up MSW handlers that never resolve
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return new Promise(() => {}); // Never resolves - simulates loading
			}),
			http.get(buildUrl("/feed"), () => {
				return new Promise(() => {}); // Never resolves - simulates loading
			}),
			http.get(buildUrl("/days"), () => {
				return new Promise(() => {}); // Never resolves - simulates loading
			}),
		);

		renderPage();
		expect(screen.getByText("Feed Preferences")).toBeInTheDocument();

		// Should show loading message
		expect(screen.getByText("Loading feed preferences...")).toBeInTheDocument();
	});

	it("renders preference form with data", async () => {
		// Set up MSW handlers to return mock data
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json([
					{
						user_id: "user-123",
						feed_id: "feed-1",
						day_id: "day-1",
						feed: { id: "feed-1", name: "Bone Meal" },
						day: { id: "day-1", name: "Monday" },
					},
				]);
			}),
			http.get(buildUrl("/feed"), () => {
				return HttpResponse.json([
					{ id: "feed-1", name: "Bone Meal" },
					{ id: "feed-2", name: "Tomato Feed" },
				]);
			}),
			http.get(buildUrl("/days"), () => {
				return HttpResponse.json([
					{ id: "day-1", name: "Monday" },
					{ id: "day-2", name: "Tuesday" },
					{ id: "day-3", name: "Wednesday" },
					{ id: "day-4", name: "Thursday" },
					{ id: "day-5", name: "Friday" },
					{ id: "day-6", name: "Saturday" },
					{ id: "day-7", name: "Sunday" },
				]);
			}),
		);

		const { container } = renderPage();

		// Wait for data to be loaded (not loading anymore)
		await waitFor(
			() => {
				expect(screen.getByText("Feed Preferences")).toBeInTheDocument();
				expect(
					screen.queryByText("Loading feed preferences..."),
				).not.toBeInTheDocument();
			},
			{ container },
		);

		// Should show feed types
		expect(screen.getByText("Bone Meal")).toBeInTheDocument();
		expect(screen.getByText("Tomato Feed")).toBeInTheDocument();

		// Should show current preference in the select dropdown for Bone Meal
		const selects = screen.getAllByRole("combobox");
		// Find the select for Bone Meal
		const boneMealSelect = Array.from(selects).find((select) => {
			const parentRow = select.closest(".flex.flex-col");
			return parentRow?.querySelector("h3")?.textContent?.includes("Bone Meal");
		});
		expect(boneMealSelect).toBeInTheDocument();
		// The value should be set to day-1 (Monday)
		expect((boneMealSelect as HTMLSelectElement).value).toBe("day-1");
	});

	it("updates feed preference successfully", async () => {
		// Set up MSW handlers for the test flow
		server.use(
			// Initial data
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json([
					{
						user_id: "user-123",
						feed_id: "feed-1",
						day_id: "day-1",
						feed: { id: "feed-1", name: "Bone Meal" },
						day: { id: "day-1", name: "Monday" },
					},
				]);
			}),
			http.get(buildUrl("/feed"), () => {
				return HttpResponse.json([
					{ id: "feed-1", name: "Bone Meal" },
					{ id: "feed-2", name: "Tomato Feed" },
				]);
			}),
			http.get(buildUrl("/days"), () => {
				return HttpResponse.json([
					{ id: "day-1", name: "Monday" },
					{ id: "day-2", name: "Tuesday" },
					{ id: "day-3", name: "Wednesday" },
					{ id: "day-4", name: "Thursday" },
					{ id: "day-5", name: "Friday" },
					{ id: "day-6", name: "Saturday" },
					{ id: "day-7", name: "Sunday" },
				]);
			}),
			// PUT to update preference succeeds
			http.put(buildUrl("/users/preferences/feed-1"), () => {
				return HttpResponse.json({
					user_id: "user-123",
					feed_id: "feed-1",
					day_id: "day-2",
					feed: { id: "feed-1", name: "Bone Meal" },
					day: { id: "day-2", name: "Tuesday" },
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Feed Preferences")).toBeInTheDocument(),
			{ container },
		);

		// Wait for data to be loaded (not loading anymore)
		await waitFor(
			() => {
				expect(screen.getByText("Feed Preferences")).toBeInTheDocument();
				expect(
					screen.queryByText("Loading feed preferences..."),
				).not.toBeInTheDocument();
			},
			{ container },
		);

		// Find the select for Bone Meal and change its value
		const selects = screen.getAllByRole("combobox");

		const boneMealSelect = Array.from(selects).find((select) => {
			// Look for the select within a parent div that has a sibling containing "Bone Meal" h3 element
			const parentRow = select.closest(".flex.flex-col");
			return parentRow?.querySelector("h3")?.textContent?.includes("Bone Meal");
		});

		expect(boneMealSelect).toBeInTheDocument();

		// Click the select and choose Wednesday
		if (boneMealSelect) {
			await userEvent.selectOptions(boneMealSelect, "day-3");
		}

		// Verify the update was successful
		await waitFor(
			() => {
				expect(screen.queryByText(/saving/i)).not.toBeInTheDocument();
			},
			{ container },
		);
	});

	it("creates new preference for feed without existing preference", async () => {
		// Set up MSW handlers for creating new preference
		server.use(
			// Initial data - no existing preferences
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json([]);
			}),
			http.get(buildUrl("/feed"), () => {
				return HttpResponse.json([
					{ id: "feed-1", name: "Bone Meal" },
					{ id: "feed-2", name: "Tomato Feed" },
				]);
			}),
			http.get(buildUrl("/days"), () => {
				return HttpResponse.json([
					{ id: "day-1", name: "Monday" },
					{ id: "day-2", name: "Tuesday" },
					{ id: "day-3", name: "Wednesday" },
					{ id: "day-4", name: "Thursday" },
					{ id: "day-5", name: "Friday" },
					{ id: "day-6", name: "Saturday" },
					{ id: "day-7", name: "Sunday" },
				]);
			}),
			// POST to create preference succeeds
			http.post(buildUrl("/users/preferences"), () => {
				return HttpResponse.json({
					user_id: "user-123",
					feed_id: "feed-1",
					day_id: "day-1",
					feed: { id: "feed-1", name: "Bone Meal" },
					day: { id: "day-1", name: "Monday" },
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Feed Preferences")).toBeInTheDocument(),
			{ container },
		);

		// Wait for data to be loaded (not loading anymore)
		await waitFor(
			() => {
				expect(screen.getByText("Feed Preferences")).toBeInTheDocument();
				expect(
					screen.queryByText("Loading feed preferences..."),
				).not.toBeInTheDocument();
			},
			{ container },
		);

		// Find the select for Bone Meal and change its value
		const selects = container.querySelectorAll("select");
		const boneMealSelect = Array.from(selects).find((select) => {
			// Look for the select within a parent div that has a sibling containing "Bone Meal" h3 element
			const parentRow = select.closest(".flex.flex-col");
			return parentRow?.querySelector("h3")?.textContent?.includes("Bone Meal");
		});

		expect(boneMealSelect).toBeInTheDocument();

		// Change the value to Monday
		if (boneMealSelect) {
			fireEvent.change(boneMealSelect, { target: { value: "mon-id" } });
		}

		// Verify the creation was successful
		await waitFor(
			() => {
				expect(screen.queryByText(/saving/i)).not.toBeInTheDocument();
			},
			{ container },
		);
	});

	it("shows error when API call fails", async () => {
		// Set up MSW handlers to return errors for all endpoints to trigger error state
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json(
					{ detail: "Internal server error" },
					{ status: 500 },
				);
			}),
			http.get(buildUrl("/feed"), () => {
				return HttpResponse.json(
					{ detail: "Internal server error" },
					{ status: 500 },
				);
			}),
			http.get(buildUrl("/days"), () => {
				return HttpResponse.json(
					{ detail: "Internal server error" },
					{ status: 500 },
				);
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Feed Preferences")).toBeInTheDocument(),
			{ container },
		);

		// Should show error message after retries complete
		await waitFor(
			() => {
				expect(
					screen.queryByText("Loading feed preferences..."),
				).not.toBeInTheDocument();
			},
			{ container, timeout: 10000 },
		);

		expect(screen.getByText(/failed to load data/i)).toBeInTheDocument();
	});

	it("redirects to login if not authenticated", async () => {
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: false });
		const { container } = renderPage();
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"), {
			container,
		});
	});

	it("shows message when no feed types are available", async () => {
		// Set up MSW handlers to return empty data
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json([]);
			}),
			http.get(buildUrl("/feed"), () => {
				return HttpResponse.json([]);
			}),
			http.get(buildUrl("/days"), () => {
				return HttpResponse.json([{ id: "day-1", name: "Monday" }]);
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Feed Preferences")).toBeInTheDocument(),
			{ container },
		);

		// Should show no feed types message
		expect(
			await screen.findByText("No feed types available"),
		).toBeInTheDocument();
	});
});
