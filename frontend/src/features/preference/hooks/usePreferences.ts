import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	getUserFeedPreferences,
	updateUserFeedPreference,
} from "../services/PreferenceService";
import type {
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
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
		staleTime: 5 * 60 * 1000, // 5 minutes
		gcTime: 10 * 60 * 1000, // 10 minutes
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
		onSuccess: () => {
			// Invalidate and refetch preferences
			queryClient.invalidateQueries({
				queryKey: PREFERENCE_QUERY_KEYS.preferences,
			});
		},
	});
};
