import { useQuery } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

export const publicGrowGuidesKey = ["publicGrowGuides"] as const;

export const usePublicGrowGuides = () => {
	return useQuery({
		queryKey: publicGrowGuidesKey,
		queryFn: growGuideService.getPublicGrowGuides,
		staleTime: 1000 * 60 * 5, // 5 minutes
	});
};
