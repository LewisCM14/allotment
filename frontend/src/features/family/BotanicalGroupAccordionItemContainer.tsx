import type * as React from "react";
import { BotanicalGroupAccordionItemPresenter } from "./BotanicalGroupAccordionItemPresenter";
import type { IBotanicalGroup } from "./FamilyService";

interface BotanicalGroupAccordionItemContainerProps {
	group: IBotanicalGroup;
}

export function BotanicalGroupAccordionItemContainer({
	group,
}: BotanicalGroupAccordionItemContainerProps) {
	// In the future, this container could hold logic specific to an item,
	// e.g., fetching more details for a family when clicked, handling item-specific state.
	return <BotanicalGroupAccordionItemPresenter group={group} />;
}
