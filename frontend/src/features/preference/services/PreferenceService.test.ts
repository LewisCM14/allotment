import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import {
	getUserFeedPreferences,
	updateUserFeedPreference,
	type IUserFeedPreference,
	type IFeedPreferenceUpdateRequest,
} from "./PreferenceService";

describe("PreferenceService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		localStorage.clear();
		vi.restoreAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("getUserFeedPreferences", () => {
		it("should fetch user feed preferences successfully", async () => {
			const mockResponse = {
				user_feed_days: [
					{
						feed_id: "feed-1",
						feed_name: "Bone Meal",
						day_id: "day-1",
						day_name: "Monday",
					},
					{
						feed_id: "feed-2",
						feed_name: "Tomato Feed",
						day_id: "day-3",
						day_name: "Wednesday",
					},
				],
				available_feeds: [
					{ id: "feed-1", name: "Bone Meal" },
					{ id: "feed-2", name: "Tomato Feed" },
				],
				available_days: [
					{ id: "day-1", day_number: 1, name: "Monday" },
					{ id: "day-3", day_number: 3, name: "Wednesday" },
				],
			};

			server.use(
				http.get(buildUrl("/users/preferences"), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await getUserFeedPreferences();
			expect(result).toEqual(mockResponse);
		});

		it("should handle server errors (500)", async () => {
			server.use(
				http.get(buildUrl("/users/preferences"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(getUserFeedPreferences()).rejects.toThrow(
				"Server error. Please try again later.",
			);
		});

		it("should handle network errors", async () => {
			Object.defineProperty(navigator, "onLine", {
				value: false,
				writable: true,
			});

			server.use(
				http.get(buildUrl("/users/preferences"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(getUserFeedPreferences()).rejects.toThrow();
		});
	});

	describe("updateUserFeedPreference", () => {
		it("should update a user feed preference successfully", async () => {
			const feedId = "feed-1";
			const mockRequest: IFeedPreferenceUpdateRequest = {
				day_id: "day-5",
			};

			const mockResponse: IUserFeedPreference = {
				user_id: "user-123",
				feed_id: "feed-1",
				day_id: "day-5",
				feed: { id: "feed-1", name: "Bone Meal" },
				day: { id: "day-5", day_number: 5, name: "Friday" },
			};

			server.use(
				http.put(
					buildUrl(`/users/preferences/${feedId}`),
					async ({ request }) => {
						const body = (await request.json()) as IFeedPreferenceUpdateRequest;
						expect(body).toEqual(mockRequest);
						return HttpResponse.json(mockResponse);
					},
				),
			);

			const result = await updateUserFeedPreference(feedId, mockRequest);
			expect(result).toEqual(mockResponse);
		});

		it("should handle not found errors (404)", async () => {
			const feedId = "nonexistent-feed";
			const mockRequest: IFeedPreferenceUpdateRequest = {
				day_id: "day-5",
			};

			server.use(
				http.put(buildUrl(`/users/preferences/${feedId}`), () => {
					return HttpResponse.json(
						{ detail: "Feed preference not found." },
						{ status: 404 },
					);
				}),
			);

			await expect(
				updateUserFeedPreference(feedId, mockRequest),
			).rejects.toThrow("Feed preference not found.");
		});

		it("should handle validation errors (422)", async () => {
			const feedId = "feed-1";
			const mockRequest: IFeedPreferenceUpdateRequest = {
				day_id: "invalid-uuid",
			};

			server.use(
				http.put(buildUrl(`/users/preferences/${feedId}`), () => {
					return HttpResponse.json(
						{
							detail: [
								{
									loc: ["body", "day_id"],
									msg: "Invalid UUID format",
									type: "value_error",
								},
							],
						},
						{ status: 422 },
					);
				}),
			);

			await expect(
				updateUserFeedPreference(feedId, mockRequest),
			).rejects.toThrow("Invalid UUID format");
		});
	});
});
