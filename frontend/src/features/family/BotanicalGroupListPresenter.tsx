import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Loader2 } from "lucide-react";
import type * as React from "react";
import { BotanicalGroupAccordionList } from "./BotanicalGroupAccordionList";
import type { IBotanicalGroup } from "./FamilyService";

interface BotanicalGroupListPresenterProps {
	botanicalGroups: IBotanicalGroup[];
	isLoading: boolean;
	error: Error | null;
}

export function BotanicalGroupListPresenter({
	botanicalGroups,
	isLoading,
	error,
}: BotanicalGroupListPresenterProps) {
	if (isLoading) {
		return (
			<div className="flex justify-center items-center h-64">
				<Loader2 className="h-8 w-8 animate-spin text-primary" />
				<p className="ml-2">Loading botanical groups...</p>
			</div>
		);
	}

	if (error) {
		return (
			<Alert variant="destructive" className="my-4">
				<AlertTitle>Error</AlertTitle>
				<AlertDescription>
					Failed to load botanical groups: {error.message}
				</AlertDescription>
			</Alert>
		);
	}

	if (botanicalGroups.length === 0) {
		return (
			<div className="text-center py-8">
				<p className="text-muted-foreground">No botanical groups found.</p>
			</div>
		);
	}

	return (
		<div className="w-full">
			<h1 className="text-3xl font-bold mb-6 text-center">Botanical Groups</h1>
			<BotanicalGroupAccordionList groups={botanicalGroups} />
		</div>
	);
}
