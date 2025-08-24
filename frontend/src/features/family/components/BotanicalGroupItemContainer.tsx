import type * as React from "react";
import { BotanicalGroupItemPresenter } from "./BotanicalGroupItemPresenter";
import type { IBotanicalGroup } from "../services/FamilyService";

interface BotanicalGroupItemContainerProps {
	readonly group: IBotanicalGroup;
	readonly onFamilyClick: (familyId: string) => void;
}

export function BotanicalGroupItemContainer({
	group,
	onFamilyClick,
}: BotanicalGroupItemContainerProps) {
	const handleFamilyClick = (familyId: string) => {
		onFamilyClick(familyId);
	};

	return (
		<BotanicalGroupItemPresenter
			group={group}
			onFamilyClick={handleFamilyClick}
		/>
	);
}
