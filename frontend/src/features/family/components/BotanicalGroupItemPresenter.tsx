import {
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/Accordion";
import { ArrowRight } from "lucide-react";
import type * as React from "react";
import type { IBotanicalGroup } from "../services/FamilyService";

interface BotanicalGroupItemPresenterProps {
	readonly group: IBotanicalGroup;
	readonly onFamilyClick: (familyId: string) => void;
}

export function BotanicalGroupItemPresenter({
	group,
	onFamilyClick,
}: BotanicalGroupItemPresenterProps) {
	const families = Array.isArray(group.families) ? group.families : [];
	return (
		<AccordionItem value={group.botanical_group_id}>
			<AccordionTrigger className="cursor-pointer">
				<div className="flex flex-col items-start text-left">
					<span className="text-lg font-semibold capitalize">
						{group.botanical_group_name}
					</span>
					<span className="text-sm text-muted-foreground">
						Recommended Rotation:{" "}
						{group.rotate_years !== null && group.rotate_years !== undefined
							? `${group.rotate_years} year(s)`
							: "Perennial"}
					</span>
				</div>
			</AccordionTrigger>
			<AccordionContent>
				{families.length > 0 ? (
					<div className="space-y-1">
						{families.map((family, idx) => (
							<button
								key={family.family_id}
								type="button"
								onClick={() => onFamilyClick(family.family_id)}
								className={[
									"group flex items-center justify-between w-full text-base text-foreground capitalize px-4 py-3 cursor-pointer transition-all rounded-md",
									"hover:bg-accent hover:shadow-sm hover:text-interactive-foreground",
									"focus:bg-accent focus:outline-none focus:text-interactive-foreground",
									idx !== families.length - 1
										? "border-b border-border/20"
										: "",
								].join(" ")}
								aria-label={`View details for ${family.family_name}`}
							>
								<span className="truncate">{family.family_name}</span>
								<ArrowRight className="size-5 text-muted-foreground group-hover:text-interactive-foreground group-focus:text-interactive-foreground transition-colors ml-2 flex-shrink-0" />
							</button>
						))}
					</div>
				) : (
					<p className="text-sm text-muted-foreground pl-6">
						No families listed for this group.
					</p>
				)}
			</AccordionContent>
		</AccordionItem>
	);
}
