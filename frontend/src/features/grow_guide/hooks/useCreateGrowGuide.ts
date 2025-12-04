import { useMutation, useQueryClient } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";
import type { GrowGuideFormData } from "../forms/GrowGuideFormSchema";

export const useCreateGrowGuide = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (data: GrowGuideFormData) => {
			return growGuideService.createGrowGuide(data);
		},
		onSuccess: () => {
			// Invalidate the grow guides query to refetch the data
			queryClient.invalidateQueries({ queryKey: ["userGrowGuides"] });
			queryClient.invalidateQueries({ queryKey: ["weeklyTodo"] });
		},
	});
};
