import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";

// Mock data
const mockFeedTypes = [
	{ id: "feed-1", name: "Bone Meal" },
	{ id: "feed-2", name: "Tomato Feed" },
	{ id: "feed-3", name: "Compost" },
	{ id: "feed-4", name: "Liquid Fertilizer" },
];

const mockDays = [
	{ id: "day-1", name: "Monday" },
	{ id: "day-2", name: "Tuesday" },
	{ id: "day-3", name: "Wednesday" },
	{ id: "day-4", name: "Thursday" },
	{ id: "day-5", name: "Friday" },
	{ id: "day-6", name: "Saturday" },
	{ id: "day-7", name: "Sunday" },
];

const mockUserPreferences = [
	{
		user_id: "user-123",
		feed_id: "feed-1",
		day_id: "day-1",
		feed: { id: "feed-1", name: "Bone Meal" },
		day: { id: "day-1", name: "Monday" },
	},
	{
		user_id: "user-123",
		feed_id: "feed-2",
		day_id: "day-3",
		feed: { id: "feed-2", name: "Tomato Feed" },
		day: { id: "day-3", name: "Wednesday" },
	},
];

export const preferenceHandlers = [
	// Get user feed preferences
	http.get(buildUrl("/users/preferences"), () => {
		return HttpResponse.json(mockUserPreferences);
	}),

	// Create user feed preference
	http.post(buildUrl("/users/preferences"), async ({ request }) => {
		const body = await request.json();
		const { feed_id, day_id } = body as { feed_id: string; day_id: string };

		const feed = mockFeedTypes.find((f) => f.id === feed_id);
		const day = mockDays.find((d) => d.id === day_id);

		if (!feed || !day) {
			return HttpResponse.json(
				{ detail: "Feed or Day not found" },
				{ status: 404 },
			);
		}

		const newPreference = {
			user_id: "user-123",
			feed_id,
			day_id,
			feed,
			day,
		};

		return HttpResponse.json(newPreference, { status: 201 });
	}),

	// Update user feed preference
	http.put(
		buildUrl("/users/preferences/:feedId"),
		async ({ params, request }) => {
			const { feedId } = params;
			const body = await request.json();
			const { day_id } = body as { day_id: string };

			const feed = mockFeedTypes.find((f) => f.id === feedId);
			const day = mockDays.find((d) => d.id === day_id);

			if (!feed || !day) {
				return HttpResponse.json(
					{ detail: "Feed preference not found" },
					{ status: 404 },
				);
			}

			const updatedPreference = {
				user_id: "user-123",
				feed_id: feedId as string,
				day_id,
				feed,
				day,
			};

			return HttpResponse.json(updatedPreference);
		},
	),

	// Get feed types
	http.get(buildUrl("/feed"), () => {
		return HttpResponse.json(mockFeedTypes);
	}),

	// Get days
	http.get(buildUrl("/days"), () => {
		return HttpResponse.json(mockDays);
	}),
];
