import api, { handleApiError } from "../../../services/api";
import type {
	IUserFeedPreference,
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
	FeedRead,
	DayRead,
	FeedDayRead,
	UserPreferencesRead,
} from "../forms/PreferenceSchema";

// Re-export types for easier importing in tests
export type {
	IUserFeedPreference,
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
	FeedRead,
	DayRead,
	FeedDayRead,
};

export class NoPreferencesFoundError extends Error {
	constructor(message = "No feed preferences found") {
		super(message);
		this.name = "NoPreferencesFoundError";
	}
}

export const getUserFeedPreferences =
	async (): Promise<UserPreferencesRead> => {
		try {
			const response = await api.get<UserPreferencesRead>("/users/preferences");
			return {
				user_feed_days: response.data.user_feed_days ?? [],
				available_feeds: response.data.available_feeds ?? [],
				available_days: response.data.available_days ?? [],
			};
		} catch (error: unknown) {
			handleApiError(
				error,
				"Failed to fetch feed preferences. Please try again.",
			);
			throw new Error("Unreachable");
		}
	};

export const updateUserFeedPreference = async (
	feedId: string,
	preferenceData: IFeedPreferenceUpdateRequest,
): Promise<IUserFeedPreference> => {
	try {
		const response = await api.put<IUserFeedPreference>(
			`/users/preferences/${feedId}`,
			preferenceData,
		);
		return response.data;
	} catch (error: unknown) {
		handleApiError(
			error,
			"Failed to update feed preference. Please try again.",
		);
		throw new Error("Unreachable");
	}
};
