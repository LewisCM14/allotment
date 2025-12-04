import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
	growGuideService,
	type VarietyList,
} from "../services/growGuideService";
import { growGuideQueryKey } from "./useGrowGuide";

// Keep key consistent with list fetching
const USER_GUIDES_KEY = ["userGrowGuides"] as const;

interface ToggleArgs {
	varietyId: string;
	currentIsPublic: boolean;
}

export const useToggleVarietyPublic = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async ({ varietyId, currentIsPublic }: ToggleArgs) => {
			return growGuideService.toggleVarietyPublic(varietyId, currentIsPublic);
		},
		// Optimistic update
		onMutate: async ({ varietyId, currentIsPublic }) => {
			await queryClient.cancelQueries({ queryKey: USER_GUIDES_KEY });
			const previous = queryClient.getQueryData<VarietyList[]>(USER_GUIDES_KEY);
			if (previous) {
				queryClient.setQueryData<VarietyList[]>(USER_GUIDES_KEY, (old) =>
					(old ?? []).map((g) =>
						g.variety_id === varietyId
							? { ...g, is_public: !currentIsPublic }
							: g,
					),
				);
			}
			return { previous };
		},
		onError: (_err, _vars, context) => {
			// Rollback
			if (context?.previous) {
				queryClient.setQueryData(USER_GUIDES_KEY, context.previous);
			}
		},
		onSuccess: (_data, { varietyId }) => {
			// Ensure server truth wins eventually
			queryClient.invalidateQueries({ queryKey: USER_GUIDES_KEY });
			queryClient.invalidateQueries({ queryKey: growGuideQueryKey(varietyId) });
		},
	});
};
