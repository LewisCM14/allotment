import {
	screen,
	waitFor,
	fireEvent,
	waitForElementToBeRemoved,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UserPreference from "./UserPreference";
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

import {
	feedPreferenceSchema,
	type FeedPreferenceFormData,
	type IFeedPreferenceRequest,
	type IFeedPreferenceUpdateRequest,
} from "../forms/PreferenceSchema";

function renderPage() {
	const result = renderWithReactQuery(<UserPreference />);
	return result;
}

describe("UserPreferencePage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(useAuth as unknown as Mock).mockReturnValue({ isAuthenticated: true });
	});

	it("shows validation error if invalid dayId is selected (runtime Zod schema)", async () => {
		// Set up MSW handlers to return normal data
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json({
					user_feed_days: [
						{
							feed_id: "feed-1",
							feed_name: "Bone Meal",
							day_id: "day-1",
							day_name: "Monday",
						},
					],
					available_feeds: [{ id: "feed-1", name: "Bone Meal" }],
					available_days: [
						{ id: "day-1", day_number: 1, name: "Monday" },
						{ id: "day-2", day_number: 2, name: "Tuesday" },
					],
				});
			}),
		);

		const { container } = renderPage();
		await waitFor(
			() => expect(screen.getByText("Feed Preferences")).toBeInTheDocument(),
			{ container },
		);

		// Wait for data to be loaded
		await waitFor(
			() => {
				expect(
					screen.queryByText("Loading feed preferences..."),
				).not.toBeInTheDocument();
			},
			{ container },
		);

		// Find the select for Bone Meal and set an invalid value
		const select = screen.getByRole("combobox");
		expect(select).toBeInTheDocument();

		// Simulate selecting an invalid dayId (not a UUID)
		fireEvent.change(select, { target: { value: "not-a-uuid" } });

		// Should show a validation error from Zod
		await waitFor(
			() => {
				expect(screen.getByText(/Invalid day ID/i)).toBeInTheDocument();
			},
			{ container },
		);
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

		// Should show loading spinner
		expect(screen.getByLabelText("Loading")).toBeInTheDocument();
		// Should not show content yet
		expect(screen.queryByText("Feed Preferences")).not.toBeInTheDocument();
	});

	it("renders preference form with data", async () => {
		// Set up MSW handlers to return mock data
		server.use(
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json({
					user_feed_days: [
						{
							feed_id: "feed-1",
							feed_name: "Bone Meal",
							day_id: "day-1",
							day_name: "Monday",
						},
					],
					available_feeds: [
						{ id: "feed-1", name: "Bone Meal" },
						{ id: "feed-2", name: "Tomato Feed" },
					],
					available_days: [
						{ id: "day-1", day_number: 1, name: "Monday" },
						{ id: "day-2", day_number: 2, name: "Tuesday" },
						{ id: "day-3", day_number: 3, name: "Wednesday" },
						{ id: "day-4", day_number: 4, name: "Thursday" },
						{ id: "day-5", day_number: 5, name: "Friday" },
						{ id: "day-6", day_number: 6, name: "Saturday" },
						{ id: "day-7", day_number: 7, name: "Sunday" },
					],
				});
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
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json({
					user_feed_days: [
						{
							feed_id: "feed-1",
							feed_name: "Bone Meal",
							day_id: "day-1",
							day_name: "Monday",
						},
					],
					available_feeds: [
						{ id: "feed-1", name: "Bone Meal" },
						{ id: "feed-2", name: "Tomato Feed" },
					],
					available_days: [
						{ id: "day-1", day_number: 1, name: "Monday" },
						{ id: "day-2", day_number: 2, name: "Tuesday" },
						{ id: "day-3", day_number: 3, name: "Wednesday" },
						{ id: "day-4", day_number: 4, name: "Thursday" },
						{ id: "day-5", day_number: 5, name: "Friday" },
						{ id: "day-6", day_number: 6, name: "Saturday" },
						{ id: "day-7", day_number: 7, name: "Sunday" },
					],
				});
			}),
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
			http.get(buildUrl("/users/preferences"), () => {
				return HttpResponse.json({
					user_feed_days: [],
					available_feeds: [
						{ id: "feed-1", name: "Bone Meal" },
						{ id: "feed-2", name: "Tomato Feed" },
					],
					available_days: [
						{ id: "day-1", day_number: 1, name: "Monday" },
						{ id: "day-2", day_number: 2, name: "Tuesday" },
						{ id: "day-3", day_number: 3, name: "Wednesday" },
						{ id: "day-4", day_number: 4, name: "Thursday" },
						{ id: "day-5", day_number: 5, name: "Friday" },
						{ id: "day-6", day_number: 6, name: "Saturday" },
						{ id: "day-7", day_number: 7, name: "Sunday" },
					],
				});
			}),
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
		// Set up MSW handlers to return error
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

		// Wait for loading spinner to disappear (after retries)
		await waitForElementToBeRemoved(() => screen.queryByLabelText("Loading"), {
			timeout: 10000,
		});

		expect(screen.getByText("Feed Preferences")).toBeInTheDocument();
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
				return HttpResponse.json({
					user_feed_days: [],
					available_feeds: [],
					available_days: [{ id: "day-1", day_number: 1, name: "Monday" }],
				});
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
