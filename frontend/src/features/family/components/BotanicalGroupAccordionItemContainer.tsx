import type * as React from "react";
import { BotanicalGroupAccordionItemPresenter } from "./BotanicalGroupAccordionItemPresenter";
import type { IBotanicalGroup } from "../services/FamilyService";

interface BotanicalGroupAccordionItemContainerProps {
	readonly group: IBotanicalGroup;
}

export function BotanicalGroupAccordionItemContainer({
	group,
}: BotanicalGroupAccordionItemContainerProps) {
	return <BotanicalGroupAccordionItemPresenter group={group} />;
}
