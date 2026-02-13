import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
	growGuideService,
	type VarietyList,
} from "../services/growGuideService";
import { growGuideQueryKey } from "./useGrowGuide";

// Query key must match list usage
const USER_GUIDES_KEY = ["userGrowGuides"] as const;

export const useDeleteVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (varietyId: string) => {
			await growGuideService.deleteVariety(varietyId);
			return varietyId;
		},
		// Optimistically remove from cache so the UI updates instantly
		onMutate: async (varietyId: string) => {
			await queryClient.cancelQueries({ queryKey: USER_GUIDES_KEY });
			const previous = queryClient.getQueryData<VarietyList[]>(USER_GUIDES_KEY);
			if (previous) {
				queryClient.setQueryData<VarietyList[]>(
					USER_GUIDES_KEY,
					previous.filter((g) => g.variety_id !== varietyId),
				);
			}
			return { previous } as { previous?: VarietyList[] };
		},
		onError: (_err, _id, context) => {
			if (context?.previous) {
				queryClient.setQueryData(USER_GUIDES_KEY, context.previous);
			}
		},
		onSuccess: (_data, varietyId) => {
			// Drop the detail cache for this variety if present
			if (typeof varietyId === "string") {
				queryClient.removeQueries({ queryKey: growGuideQueryKey(varietyId) });
			}
			// Force a full reload so the list is definitely up-to-date post-delete.
			if (
				globalThis.window !== undefined &&
				typeof globalThis.window.location?.reload === "function" &&
				import.meta.env.MODE !== "test"
			) {
				globalThis.window.location.reload();
			}
		},
		onSettled: () => {
			// Invalidate so list refetches and stays in sync with server
			queryClient.invalidateQueries({ queryKey: USER_GUIDES_KEY });
			queryClient.refetchQueries({ queryKey: USER_GUIDES_KEY });
			// Invalidate weekly todo as a variety (potentially active) was deleted
			queryClient.invalidateQueries({ queryKey: ["weeklyTodo"] });
		},
	});
};
