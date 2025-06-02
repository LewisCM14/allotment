import {
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/Accordion";
import type * as React from "react";
import type { IBotanicalGroup } from "./familyService";

interface BotanicalGroupAccordionItemPresenterProps {
	group: IBotanicalGroup;
}

export function BotanicalGroupAccordionItemPresenter({
	group,
}: BotanicalGroupAccordionItemPresenterProps) {
	return (
		<AccordionItem value={group.id}>
			<AccordionTrigger>
				<div className="flex flex-col items-start text-left">
					<span className="text-lg font-semibold">{group.name}</span>
					{group.recommended_rotation_years !== null && (
						<span className="text-sm text-muted-foreground">
							Recommended Rotation: {group.recommended_rotation_years} year(s)
						</span>
					)}
				</div>
			</AccordionTrigger>
			<AccordionContent>
				{group.families.length > 0 ? (
					<ul className="list-disc pl-6 space-y-1">
						{group.families.map((family) => (
							<li key={family.id} className="text-sm">
								{family.name}
								{/* Future: Link to family detail page, e.g., using React Router's Link */}
								{/* <Link to={`/families/${family.id}`} className="text-primary hover:underline ml-2">Details</Link> */}
							</li>
						))}
					</ul>
				) : (
					<p className="text-sm text-muted-foreground">
						No families listed for this group.
					</p>
				)}
			</AccordionContent>
		</AccordionItem>
	);
}
