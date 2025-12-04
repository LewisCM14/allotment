import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	getUserAllotment,
	createUserAllotment,
	updateUserAllotment,
	NoAllotmentFoundError,
	type IAllotmentResponse,
	type IAllotmentUpdateRequest,
} from "../services/AllotmentService";

export const userAllotmentKeys = {
	all: ["user-allotment"] as const,
	detail: () => [...userAllotmentKeys.all, "detail"] as const,
};

/**
 * Hook to fetch user allotment data with React Query
 */
export const useUserAllotment = () => {
	return useQuery<IAllotmentResponse, Error>({
		queryKey: userAllotmentKeys.detail(),
		queryFn: getUserAllotment,
		staleTime: 1000 * 60 * 60, // 1 hour
		gcTime: 1000 * 60 * 60 * 24, // 24 hours
		retry: (failureCount, error) => {
			// Don't retry on 404 (no allotment exists) or auth errors
			if (error instanceof NoAllotmentFoundError) return false;
			if (error.message.includes("Invalid email or password")) return false;
			if (error.message.includes("401")) return false;

			// Retry up to 3 times for other errors
			return failureCount < 3;
		},
		retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
	});
};

/**
 * Hook to create user allotment with optimistic updates
 */
export const useCreateUserAllotment = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: createUserAllotment,
		onSuccess: (data: IAllotmentResponse) => {
			// Update the cache with the new allotment
			queryClient.setQueryData(userAllotmentKeys.detail(), data);
		},
		onError: (error) => {
			// Error handling is managed by the calling component
		},
	});
};

/**
 * Hook to update user allotment with optimistic updates
 */
export const useUpdateUserAllotment = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: updateUserAllotment,
		onMutate: async (newAllotment: IAllotmentUpdateRequest) => {
			// Cancel any outgoing refetches
			await queryClient.cancelQueries({ queryKey: userAllotmentKeys.detail() });

			// Snapshot the previous value
			const previousAllotment = queryClient.getQueryData<IAllotmentResponse>(
				userAllotmentKeys.detail(),
			);

			// Optimistically update to the new value
			if (previousAllotment) {
				queryClient.setQueryData<IAllotmentResponse>(
					userAllotmentKeys.detail(),
					{ ...previousAllotment, ...newAllotment },
				);
			}

			// Return a context object with the snapshotted value
			return { previousAllotment };
		},
		onError: (error, newAllotment, context) => {
			// If the mutation fails, use the context returned from onMutate to roll back
			if (context?.previousAllotment) {
				queryClient.setQueryData(
					userAllotmentKeys.detail(),
					context.previousAllotment,
				);
			}
			// Error handling is managed by the calling component
		},
		onSuccess: (data) => {
			// Update the cache with the final response from the server
			queryClient.setQueryData(userAllotmentKeys.detail(), data);
		},
	});
};
