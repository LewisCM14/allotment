import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	checkEmailVerificationStatus,
	requestVerificationEmail,
} from "../services/UserService";

// Query key factory for user profile queries
export const userProfileKeys = {
	all: ["user-profile"] as const,
	verification: (email: string) =>
		[...userProfileKeys.all, "verification", email] as const,
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
		onSuccess: (data, email) => {
			// Don't optimistically update verification status since email needs to be clicked
			// Just show success message to user
		},
		onError: (error) => {
			// Error handling is managed by the calling component
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
			// Error handling is managed by the calling component
		},
	});
};
