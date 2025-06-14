import { Accordion } from "@/components/ui/Accordion";
import type * as React from "react";
import { BotanicalGroupAccordionItemContainer } from "./BotanicalGroupAccordionItemContainer";
import type { IBotanicalGroup } from "../services/FamilyService";
interface BotanicalGroupAccordionListProps {
	groups: IBotanicalGroup[];
}

export function BotanicalGroupAccordionList({
	groups,
}: BotanicalGroupAccordionListProps) {
	return (
		<Accordion type="multiple" className="w-full space-y-2">
			{groups.map((group) => (
				<BotanicalGroupAccordionItemContainer key={group.id} group={group} />
			))}
		</Accordion>
	);
}
