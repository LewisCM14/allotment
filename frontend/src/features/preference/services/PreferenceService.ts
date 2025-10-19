import api, { handleApiError } from "../../../services/api";
import type {
	IUserFeedPreference,
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
	UserPreferencesRead,
} from "../forms/PreferenceSchema";

// Re-export types for easier importing in tests
export type {
	IUserFeedPreference,
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
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
			// Normalize API payload to the shapes expected by the UI with safe typing
			const raw = response.data as unknown as Record<string, unknown>;

			const user_feed_days = Array.isArray(
				(raw as Record<string, unknown>)?.user_feed_days,
			)
				? ((raw as Record<string, unknown>)
						.user_feed_days as UserPreferencesRead["user_feed_days"])
				: [];

			// Map feeds to { id, name }
			const available_feeds = Array.isArray(
				(raw as Record<string, unknown>)?.available_feeds,
			)
				? (
						(raw as Record<string, unknown>).available_feeds as Array<unknown>
					).map((f) => {
						const feed = f as {
							id?: string;
							feed_id?: string;
							name?: string;
							feed_name?: string;
						};
						return {
							id: feed.id ?? feed.feed_id ?? "",
							name: feed.name ?? feed.feed_name ?? "",
						};
					})
				: [];

			// Map days to { id, name } and preserve day_number when present
			const available_days = Array.isArray(
				(raw as Record<string, unknown>)?.available_days,
			)
				? (
						(raw as Record<string, unknown>).available_days as Array<unknown>
					).map((d) => {
						const day = d as {
							id?: string;
							day_id?: string;
							name?: string;
							day_name?: string;
							day_number?: number;
						};
						return {
							id: day.id ?? day.day_id ?? "",
							name: day.name ?? day.day_name ?? "",
							...(day.day_number !== undefined
								? { day_number: day.day_number }
								: {}),
						};
					})
				: [];

			return {
				user_feed_days,
				available_feeds,
				available_days,
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
