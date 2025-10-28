import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
	growGuideService,
	type VarietyList,
} from "../services/growGuideService";
import { growGuideQueryKey } from "./useGrowGuide";

interface ToggleActiveVariables {
	varietyId: string;
	makeActive: boolean;
}

export const useToggleActiveVariety = () => {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async ({ varietyId, makeActive }: ToggleActiveVariables) => {
			if (makeActive) {
				return await growGuideService.activateUserGrowGuide(varietyId);
			}
			return await growGuideService.deactivateUserGrowGuide(varietyId);
		},
		onSuccess: (_data, variables) => {
			const { varietyId, makeActive } = variables;

			queryClient.setQueryData<VarietyList[] | undefined>(
				["userGrowGuides"],
				(old) =>
					old?.map((guide) =>
						guide.variety_id === varietyId
							? { ...guide, is_active: makeActive }
							: guide,
					),
			);

			queryClient.setQueryData(growGuideQueryKey(varietyId), (old: unknown) => {
				if (old && typeof old === "object") {
					return { ...old, is_active: makeActive } as typeof old;
				}
				return old;
			});
		},
	});
};
