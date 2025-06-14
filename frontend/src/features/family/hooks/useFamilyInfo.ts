import { useQuery } from "@tanstack/react-query";
import { getFamilyInfo } from "../services/FamilyService";
import type { IFamilyInfo } from "../services/FamilyService";

export function useFamilyInfo(familyId?: string) {
	return useQuery<IFamilyInfo, Error>({
		queryKey: ["familyInfo", familyId],
		queryFn: ({ signal }) => {
			if (!familyId) throw new Error("Family ID is required");
			return getFamilyInfo(familyId, signal);
		},
		enabled: !!familyId,
		staleTime: 1000 * 60 * 10, // 10 minutes
		refetchOnWindowFocus: false,
		retry: 1,
		placeholderData: (prevData) => prevData,
	});
}
