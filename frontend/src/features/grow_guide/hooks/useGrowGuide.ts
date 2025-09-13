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
	});
};

export const growGuideQueryKey = growGuideKey;
