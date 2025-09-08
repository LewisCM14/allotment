import { useQuery } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

export const useGrowGuideOptions = () => {
	return useQuery({
		queryKey: ["growGuideOptions"],
		queryFn: growGuideService.getGrowGuideOptions,
		staleTime: 1000 * 60 * 30, // 30 minutes - options don't change often
	});
};
