import { useQuery } from "@tanstack/react-query";
import { getBotanicalGroups } from "../services/FamilyService";
import type { IBotanicalGroup } from "../services/FamilyService";

export function useBotanicalGroups() {
	return useQuery<IBotanicalGroup[], Error>({
		queryKey: ["botanicalGroups"],
		queryFn: ({ signal }) => getBotanicalGroups(signal),
		staleTime: 1000 * 60 * 60 * 24, // 24 hours
		gcTime: 1000 * 60 * 60 * 24, // 24 hours
		refetchOnWindowFocus: false,
		retry: 2,
		placeholderData: (prevData) => prevData,
		select: (data) => data || [],
	});
}
