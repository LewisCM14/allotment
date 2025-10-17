import { useUserGrowGuides } from "../hooks/useUserGrowGuides";
import { GrowGuideListPresenter } from "./GrowGuideListPresenter";

interface GrowGuideListContainerProps {
	onSelect?: (varietyId: string) => void;
	selectedVarietyId?: string | null;
	onAddNew?: () => void;
}

export const GrowGuideListContainer = ({
	onSelect,
	selectedVarietyId,
	onAddNew,
}: GrowGuideListContainerProps) => {
	const { data: growGuides, isLoading, isError } = useUserGrowGuides();

	// When data is available but empty, it's not an error - it means the user has no guides
	const hasNoGuides =
		!isLoading &&
		!isError &&
		Array.isArray(growGuides) &&
		growGuides.length === 0;

	return (
		<GrowGuideListPresenter
			growGuides={growGuides || []}
			isLoading={isLoading}
			isError={isError && !hasNoGuides} // Only treat as error if not just an empty array
			onSelect={onSelect}
			selectedVarietyId={selectedVarietyId}
			onAddNew={onAddNew}
		/>
	);
};
