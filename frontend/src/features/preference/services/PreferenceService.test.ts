import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import {
    getUserFeedPreferences,
    createUserFeedPreference,
    updateUserFeedPreference,
    getFeedTypes,
    getDays,
    type IUserFeedPreference,
    type IFeedPreferenceRequest,
    type IFeedPreferenceUpdateRequest,
    type IFeedType,
    type IDay,
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
            const mockResponse: IUserFeedPreference[] = [
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

    describe("createUserFeedPreference", () => {
        it("should create a user feed preference successfully", async () => {
            const mockRequest: IFeedPreferenceRequest = {
                feed_id: "feed-1",
                day_id: "day-2",
            };

            const mockResponse: IUserFeedPreference = {
                user_id: "user-123",
                feed_id: "feed-1",
                day_id: "day-2",
                feed: { id: "feed-1", name: "Bone Meal" },
                day: { id: "day-2", name: "Tuesday" },
            };

            server.use(
                http.post(buildUrl("/users/preferences"), async ({ request }) => {
                    const body = (await request.json()) as IFeedPreferenceRequest;
                    expect(body).toEqual(mockRequest);
                    return HttpResponse.json(mockResponse);
                }),
            );

            const result = await createUserFeedPreference(mockRequest);
            expect(result).toEqual(mockResponse);
        });

        it("should handle validation errors (422)", async () => {
            const mockRequest: IFeedPreferenceRequest = {
                feed_id: "invalid-uuid",
                day_id: "invalid-uuid",
            };

            server.use(
                http.post(buildUrl("/users/preferences"), () => {
                    return HttpResponse.json(
                        {
                            detail: [
                                {
                                    loc: ["body", "feed_id"],
                                    msg: "Invalid UUID format",
                                    type: "value_error",
                                },
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

            await expect(createUserFeedPreference(mockRequest)).rejects.toThrow(
                "Invalid UUID format",
            );
        });

        it("should handle server errors (500)", async () => {
            const mockRequest: IFeedPreferenceRequest = {
                feed_id: "feed-1",
                day_id: "day-2",
            };

            server.use(
                http.post(buildUrl("/users/preferences"), () => {
                    return HttpResponse.json(
                        { detail: "Internal server error" },
                        { status: 500 },
                    );
                }),
            );

            await expect(createUserFeedPreference(mockRequest)).rejects.toThrow(
                "Server error. Please try again later.",
            );
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
                day: { id: "day-5", name: "Friday" },
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

    describe("getFeedTypes", () => {
        it("should fetch feed types successfully", async () => {
            const mockResponse: IFeedType[] = [
                { id: "feed-1", name: "Bone Meal" },
                { id: "feed-2", name: "Tomato Feed" },
                { id: "feed-3", name: "Compost" },
            ];

            server.use(
                http.get(buildUrl("/feed"), () => {
                    return HttpResponse.json(mockResponse);
                }),
            );

            const result = await getFeedTypes();
            expect(result).toEqual(mockResponse);
        });

        it("should handle server errors (500)", async () => {
            server.use(
                http.get(buildUrl("/feed"), () => {
                    return HttpResponse.json(
                        { detail: "Internal server error" },
                        { status: 500 },
                    );
                }),
            );

            await expect(getFeedTypes()).rejects.toThrow(
                "Server error. Please try again later.",
            );
        });
    });

    describe("getDays", () => {
        it("should fetch days successfully", async () => {
            const mockResponse: IDay[] = [
                { id: "day-1", name: "Monday" },
                { id: "day-2", name: "Tuesday" },
                { id: "day-3", name: "Wednesday" },
                { id: "day-4", name: "Thursday" },
                { id: "day-5", name: "Friday" },
                { id: "day-6", name: "Saturday" },
                { id: "day-7", name: "Sunday" },
            ];

            server.use(
                http.get(buildUrl("/days"), () => {
                    return HttpResponse.json(mockResponse);
                }),
            );

            const result = await getDays();
            expect(result).toEqual(mockResponse);
        });

        it("should handle authentication errors (401)", async () => {
            server.use(
                http.get(buildUrl("/days"), () => {
                    return HttpResponse.json(
                        { detail: "Not authenticated" },
                        { status: 401 },
                    );
                }),
            );

            await expect(getDays()).rejects.toThrow(
                "Invalid email or password. Please try again.",
            );
        });

        it("should handle server errors (500)", async () => {
            server.use(
                http.get(buildUrl("/days"), () => {
                    return HttpResponse.json(
                        { detail: "Internal server error" },
                        { status: 500 },
                    );
                }),
            );

            await expect(getDays()).rejects.toThrow(
                "Server error. Please try again later.",
            );
        });

        it("should handle network errors", async () => {
            Object.defineProperty(navigator, "onLine", {
                value: false,
                writable: true,
            });

            server.use(
                http.get(buildUrl("/days"), () => {
                    return HttpResponse.error();
                }),
            );

            await expect(getDays()).rejects.toThrow();
        });
    });
});
