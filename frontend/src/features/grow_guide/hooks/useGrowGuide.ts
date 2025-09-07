import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
	copyPublicVariety,
	createVariety,
	deleteVariety,
	getPublicVarieties,
	getUserVarieties,
	getVariety,
	getVarietyOptions,
	setVarietyWaterDays,
	toggleVarietyPublic,
	updateVariety,
} from "../services/growGuideService";
import type {
	VarietyCreate,
	VarietyUpdate,
} from "../types/growGuideTypes";
import { errorMonitor } from "@/services/errorMonitoring";
import { formatError } from "@/utils/errorUtils";

// Query keys
export const growGuideKeys = {
	all: ["growGuide"] as const,
	varieties: () => [...growGuideKeys.all, "varieties"] as const,
	userVarieties: () => [...growGuideKeys.varieties(), "user"] as const,
	publicVarieties: () => [...growGuideKeys.varieties(), "public"] as const,
	variety: (id: string) => [...growGuideKeys.varieties(), id] as const,
	options: () => [...growGuideKeys.all, "options"] as const,
};

// Hooks for fetching data
export const useVarietyOptions = () => {
	return useQuery({
		queryKey: growGuideKeys.options(),
		queryFn: getVarietyOptions,
		staleTime: 5 * 60 * 1000, // 5 minutes
		gcTime: 10 * 60 * 1000, // 10 minutes
		retry: 2,
	});
};

export const useUserVarieties = () => {
	return useQuery({
		queryKey: growGuideKeys.userVarieties(),
		queryFn: getUserVarieties,
		staleTime: 1 * 60 * 1000, // 1 minute
		gcTime: 5 * 60 * 1000, // 5 minutes
		retry: 2,
	});
};

export const usePublicVarieties = () => {
	return useQuery({
		queryKey: growGuideKeys.publicVarieties(),
		queryFn: getPublicVarieties,
		staleTime: 5 * 60 * 1000, // 5 minutes
		gcTime: 10 * 60 * 1000, // 10 minutes
		retry: 2,
	});
};

export const useVariety = (varietyId: string) => {
	return useQuery({
		queryKey: growGuideKeys.variety(varietyId),
		queryFn: () => getVariety(varietyId),
		enabled: !!varietyId,
		staleTime: 30 * 1000, // 30 seconds
		gcTime: 5 * 60 * 1000, // 5 minutes
		retry: 2,
	});
};

// Mutation hooks
export const useCreateVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (varietyData: VarietyCreate) =>
			createVariety(varietyData),
		onSuccess: (data) => {
			// Invalidate and refetch user varieties
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.userVarieties(),
			});
			
			// Set the newly created variety in cache
			queryClient.setQueryData(
				growGuideKeys.variety(data.variety_id),
				data,
			);

			toast.success("Grow guide created successfully!", {
				description: `${data.variety_name} has been added to your guides`,
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.create",
				url: window.location.href,
			});
			toast.error("Failed to create grow guide", {
				description: errorMessage,
			});
		},
	});
};

export const useUpdateVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: ({
			varietyId,
			varietyData,
		}: {
			varietyId: string;
			varietyData: VarietyUpdate;
		}) => updateVariety(varietyId, varietyData),
		onSuccess: (data, variables) => {
			// Update the specific variety in cache
			queryClient.setQueryData(
				growGuideKeys.variety(variables.varietyId),
				data,
			);

			// Invalidate user varieties to refresh the list
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.userVarieties(),
			});

			toast.success("Grow guide updated successfully!", {
				description: `${data.variety_name} has been updated`,
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.update",
				url: window.location.href,
			});
			toast.error("Failed to update grow guide", {
				description: errorMessage,
			});
		},
	});
};

export const useDeleteVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (varietyId: string) => deleteVariety(varietyId),
		onSuccess: (_, varietyId) => {
			// Remove the variety from cache
			queryClient.removeQueries({
				queryKey: growGuideKeys.variety(varietyId),
			});

			// Invalidate user varieties to refresh the list
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.userVarieties(),
			});

			toast.success("Grow guide deleted successfully", {
				description: "The grow guide has been removed",
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.delete",
				url: window.location.href,
			});
			toast.error("Failed to delete grow guide", {
				description: errorMessage,
			});
		},
	});
};

export const useUpdateVarietyWaterDays = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: ({
			varietyId,
			waterDays,
		}: {
			varietyId: string;
			waterDays: string[];
		}) => setVarietyWaterDays(varietyId, waterDays),
		onSuccess: (_, variables) => {
			// Invalidate the specific variety to refetch updated water days
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.variety(variables.varietyId),
			});

			toast.success("Watering days updated successfully", {
				description: "Your watering schedule has been updated",
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.updateWaterDays",
				url: window.location.href,
			});
			toast.error("Failed to update watering days", {
				description: errorMessage,
			});
		},
	});
};

export const useCopyPublicVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (varietyId: string) =>
			copyPublicVariety(varietyId),
		onSuccess: (data) => {
			// Invalidate user varieties to show the new copy
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.userVarieties(),
			});

			// Set the copied variety in cache
			queryClient.setQueryData(
				growGuideKeys.variety(data.variety_id),
				data,
			);

			toast.success("Grow guide copied successfully!", {
				description: `${data.variety_name} has been added to your guides`,
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.copy",
				url: window.location.href,
			});
			toast.error("Failed to copy grow guide", {
				description: errorMessage,
			});
		},
	});
};

export const useToggleVarietyPublic = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (varietyId: string) =>
			toggleVarietyPublic(varietyId),
		onSuccess: (data) => {
			// Update the specific variety in cache
			queryClient.setQueryData(
				growGuideKeys.variety(data.variety_id),
				data,
			);

			// Invalidate user varieties to refresh the list
			queryClient.invalidateQueries({
				queryKey: growGuideKeys.userVarieties(),
			});

			// Invalidate public varieties if it's now public
			if (data.is_public) {
				queryClient.invalidateQueries({
					queryKey: growGuideKeys.publicVarieties(),
				});
			}

			const status = data.is_public ? "public" : "private";
			toast.success(`Grow guide is now ${status}`, {
				description: `${data.variety_name} visibility has been updated`,
			});
		},
		onError: (error: unknown) => {
			const errorMessage = formatError(error);
			errorMonitor.captureException(error, {
				context: "growGuide.togglePublic",
				url: window.location.href,
			});
			toast.error("Failed to update grow guide visibility", {
				description: errorMessage,
			});
		},
	});
};
