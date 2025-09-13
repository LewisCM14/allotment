import { useMutation, useQueryClient } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

// Query key must match list usage
const USER_GUIDES_KEY = ["userGrowGuides"] as const;

export const useDeleteVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (varietyId: string) => {
			await growGuideService.deleteVariety(varietyId);
			return varietyId;
		},
		onSuccess: () => {
			// Invalidate so list refetches
			queryClient.invalidateQueries({ queryKey: USER_GUIDES_KEY });
		},
	});
};
