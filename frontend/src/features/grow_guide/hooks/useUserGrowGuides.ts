import { useQuery } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

export const useUserGrowGuides = () => {
	return useQuery({
		queryKey: ["userGrowGuides"],
		queryFn: growGuideService.getUserGrowGuides,
	});
};
