import { useQuery } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

// Cache key factory to avoid typos
const growGuideKey = (varietyId: string | undefined) =>
	["growGuide", varietyId] as const;

export const useGrowGuide = (varietyId: string | undefined) => {
	return useQuery({
		queryKey: growGuideQueryKey(varietyId),
		queryFn: () => {
			if (!varietyId) throw new Error("varietyId is required");
			return growGuideService.getGrowGuide(varietyId);
		},
		enabled: !!varietyId,
		staleTime: 1000 * 60 * 60, // 1 hour
		gcTime: 1000 * 60 * 60 * 24, // 24 hours
	});
};

export const growGuideQueryKey = growGuideKey;
