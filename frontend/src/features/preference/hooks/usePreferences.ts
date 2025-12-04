import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	getUserFeedPreferences,
	updateUserFeedPreference,
} from "../services/PreferenceService";
import type {
	IFeedPreferenceUpdateRequest,
	UserPreferencesRead,
} from "../forms/PreferenceSchema";

// Query keys
export const PREFERENCE_QUERY_KEYS = {
	preferences: ["userPreferencesAggregate"] as const,
};

// Hook for fetching all user preferences aggregate (preferences, feedTypes, days)
export const useUserPreferencesAggregate = () => {
	return useQuery({
		queryKey: PREFERENCE_QUERY_KEYS.preferences,
		queryFn: getUserFeedPreferences,
		staleTime: 1000 * 60 * 60, // 1 hour
		gcTime: 1000 * 60 * 60 * 24, // 24 hours
	});
};

// Hook for updating a user feed preference
export const useUpdateUserFeedPreference = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: ({
			feedId,
			data,
		}: {
			feedId: string;
			data: IFeedPreferenceUpdateRequest;
		}) => updateUserFeedPreference(feedId, data),
		onSuccess: (data, variables) => {
			// Optimistically update the cache with the new preference
			queryClient.setQueryData<UserPreferencesRead>(
				PREFERENCE_QUERY_KEYS.preferences,
				(oldData) => {
					if (!oldData) return oldData;

					// Find if the preference already exists
					const existingPrefIndex = oldData.user_feed_days.findIndex(
						(p) => p.feed_id === variables.feedId,
					);

					const newFeedDays = [...oldData.user_feed_days];

					if (existingPrefIndex >= 0) {
						// Update existing preference
						newFeedDays[existingPrefIndex] = {
							...newFeedDays[existingPrefIndex],
							day_id: variables.data.day_id,
						};
					} else {
						queryClient.invalidateQueries({
							queryKey: PREFERENCE_QUERY_KEYS.preferences,
						});
						return oldData;
					}

					return {
						...oldData,
						user_feed_days: newFeedDays,
					};
				},
			);
		},
	});
};
