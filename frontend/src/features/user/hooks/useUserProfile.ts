import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { errorMonitor } from "@/services/errorMonitoring";
import {
	checkEmailVerificationStatus,
	getUserProfile,
	requestVerificationEmail,
	updateUserProfile,
	type UserProfileUpdate,
} from "../services/UserService";

// Query key factory for user profile queries
export const userProfileKeys = {
	all: ["user-profile"] as const,
	profile: () => [...userProfileKeys.all, "profile"] as const,
	verification: (email: string) =>
		[...userProfileKeys.all, "verification", email] as const,
};

/**
 * Hook to get user profile information
 */
export const useUserProfile = () => {
	return useQuery({
		queryKey: userProfileKeys.profile(),
		queryFn: getUserProfile,
		staleTime: 1000 * 60 * 60, // 1 hour
		gcTime: 1000 * 60 * 60 * 24, // 24 hours
		retry: (failureCount, error) => {
			// Don't retry on auth errors
			if (
				error?.message?.includes("401") ||
				error?.message?.includes("Invalid")
			) {
				return false;
			}
			return failureCount < 2;
		},
	});
};

/**
 * Hook to update user profile with optimistic updates
 */
export const useUpdateUserProfile = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: updateUserProfile,
		onMutate: async (newProfileData: UserProfileUpdate) => {
			// Cancel outgoing queries
			await queryClient.cancelQueries({ queryKey: userProfileKeys.profile() });

			// Get previous profile data
			const previousProfile = queryClient.getQueryData(
				userProfileKeys.profile(),
			);

			// Optimistically update the profile
			if (previousProfile) {
				queryClient.setQueryData(userProfileKeys.profile(), {
					...previousProfile,
					...newProfileData,
				});
			}

			// Return context for rollback
			return { previousProfile };
		},
		onError: (error, variables, context) => {
			// Rollback on error
			if (context?.previousProfile) {
				queryClient.setQueryData(
					userProfileKeys.profile(),
					context.previousProfile,
				);
			}

			// Log the error for monitoring
			errorMonitor.captureException(error, {
				context: "useUpdateUserProfile.mutation",
				variables: variables,
				url: globalThis.location.href,
			});
		},
		onSuccess: (data) => {
			// Update the cache with the server response
			queryClient.setQueryData(userProfileKeys.profile(), data);
		},
	});
};

/**
 * Hook to check email verification status
 */
export const useEmailVerificationStatus = (email?: string) => {
	return useQuery({
		queryKey: userProfileKeys.verification(email ?? ""),
		queryFn: () => {
			if (!email) throw new Error("Email is required");
			return checkEmailVerificationStatus(email);
		},
		enabled: !!email,
		staleTime: 2 * 60 * 1000, // 2 minutes - verification status can change quickly
		gcTime: 5 * 60 * 1000, // 5 minutes cache time
		retry: (failureCount, error) => {
			// Don't retry on auth errors
			if (
				error?.message?.includes("401") ||
				error?.message?.includes("Invalid")
			) {
				return false;
			}
			return failureCount < 2; // Only retry once for verification checks
		},
		refetchOnWindowFocus: true, // Good for verification status
	});
};

/**
 * Hook to request email verification with optimistic updates
 */
export const useRequestEmailVerification = () => {
	return useMutation({
		mutationFn: requestVerificationEmail,
		onSuccess: (_data, _email) => {
			// Don't optimistically update verification status since email needs to be clicked
			// Just show success message to user
		},
		onError: (error) => {
			// Log the error for monitoring
			errorMonitor.captureException(error, {
				context: "useRequestEmailVerification.mutation",
				url: globalThis.location.href,
			});
		},
	});
};

/**
 * Hook to manually refresh verification status
 */
export const useRefreshVerificationStatus = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (email: string) => checkEmailVerificationStatus(email),
		onSuccess: (data, email) => {
			// Update the cache with fresh verification status
			queryClient.setQueryData(userProfileKeys.verification(email), data);

			// If verified, invalidate to ensure fresh data
			if (data.is_email_verified) {
				queryClient.invalidateQueries({
					queryKey: userProfileKeys.all,
				});
			}
		},
		onError: (error) => {
			// Log the error for monitoring
			errorMonitor.captureException(error, {
				context: "useRefreshVerificationStatus.mutation",
				url: globalThis.location.href,
			});
		},
	});
};
