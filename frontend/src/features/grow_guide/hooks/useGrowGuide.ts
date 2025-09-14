import { useQuery } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

// Cache key factory to avoid typos
const growGuideKey = (varietyId: string | undefined) =>
	["growGuide", varietyId] as const;

export const useGrowGuide = (varietyId: string | undefined) => {
	return useQuery({
		queryKey: growGuideKey(varietyId),
		queryFn: () => {
			if (!varietyId) throw new Error("varietyId is required");
			return growGuideService.getGrowGuide(varietyId);
		},
		enabled: !!varietyId,
		// Ensure fresh data when switching between guides
		refetchOnMount: "always",
		// Keep cache relatively fresh to avoid stale data issues
		staleTime: 30 * 1000, // 30 seconds
	});
};

export const growGuideQueryKey = growGuideKey;
