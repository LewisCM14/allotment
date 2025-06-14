import {
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/Accordion";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type * as React from "react";
import type { IBotanicalGroup } from "../services/FamilyService";

interface BotanicalGroupAccordionItemPresenterProps {
	group: IBotanicalGroup;
}

export function BotanicalGroupAccordionItemPresenter({
	group,
}: BotanicalGroupAccordionItemPresenterProps) {
	const navigate = useNavigate();
	return (
		<AccordionItem value={group.id}>
			<AccordionTrigger>
				<div className="flex flex-col items-start text-left">
					<span className="text-lg font-semibold capitalize">{group.name}</span>
					<span className="text-sm text-muted-foreground">
						Recommended Rotation:{" "}
						{group.recommended_rotation_years !== null
							? `${group.recommended_rotation_years} year(s)`
							: "Perennial"}
					</span>
				</div>
			</AccordionTrigger>
			<AccordionContent>
				{group.families.length > 0 ? (
					<div className="space-y-1">
						{group.families.map((family, idx) => (
							<button
								key={family.id}
								type="button"
								onClick={() => navigate(`/family/${family.id}`)}
								className={[
									"group flex items-center justify-between w-full text-base text-foreground capitalize px-4 py-3 cursor-pointer transition-all rounded-md",
									"hover:bg-accent hover:shadow-sm hover:text-interactive-foreground",
									"focus:bg-accent focus:outline-none focus:text-interactive-foreground",
									idx !== group.families.length - 1
										? "border-b border-border/20"
										: "",
								].join(" ")}
								aria-label={`View details for ${family.name}`}
							>
								<span className="truncate">{family.name}</span>
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
