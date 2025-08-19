import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	getUserFeedPreferences,
	createUserFeedPreference,
	updateUserFeedPreference,
	getFeedTypes,
	getDays,
} from "../services/PreferenceService";
import type {
	IFeedPreferenceRequest,
	IFeedPreferenceUpdateRequest,
} from "../forms/PreferenceSchema";

// Query keys
export const PREFERENCE_QUERY_KEYS = {
	preferences: ["userFeedPreferences"] as const,
	feedTypes: ["feedTypes"] as const,
	days: ["days"] as const,
};

// Hook for fetching user feed preferences
export const useUserFeedPreferences = () => {
	return useQuery({
		queryKey: PREFERENCE_QUERY_KEYS.preferences,
		queryFn: getUserFeedPreferences,
		staleTime: 5 * 60 * 1000, // 5 minutes
		gcTime: 10 * 60 * 1000, // 10 minutes
	});
};

// Hook for fetching feed types
export const useFeedTypes = () => {
	return useQuery({
		queryKey: PREFERENCE_QUERY_KEYS.feedTypes,
		queryFn: getFeedTypes,
		staleTime: 60 * 60 * 1000, // 1 hour (reference data doesn't change often)
		gcTime: 2 * 60 * 60 * 1000, // 2 hours
	});
};

// Hook for fetching days
export const useDays = () => {
	return useQuery({
		queryKey: PREFERENCE_QUERY_KEYS.days,
		queryFn: getDays,
		staleTime: 60 * 60 * 1000, // 1 hour (reference data doesn't change often)
		gcTime: 2 * 60 * 60 * 1000, // 2 hours
	});
};

// Hook for creating a user feed preference
export const useCreateUserFeedPreference = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (data: IFeedPreferenceRequest) =>
			createUserFeedPreference(data),
		onSuccess: () => {
			// Invalidate and refetch preferences
			queryClient.invalidateQueries({
				queryKey: PREFERENCE_QUERY_KEYS.preferences,
			});
		},
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
