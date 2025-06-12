import { useQuery } from "@tanstack/react-query";
import { getBotanicalGroups } from "../FamilyService";
import type { IBotanicalGroup } from "../FamilyService";

export function useBotanicalGroups() {
	return useQuery<IBotanicalGroup[], Error>({
		queryKey: ["botanicalGroups"],
		queryFn: ({ signal }) => getBotanicalGroups(signal),
		staleTime: 1000 * 60 * 5,
		refetchOnWindowFocus: false,
		retry: 2,
		placeholderData: (prevData) => prevData,
		select: (data) => data || [],
	});
}
