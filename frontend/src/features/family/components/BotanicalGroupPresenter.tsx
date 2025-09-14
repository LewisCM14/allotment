import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Accordion } from "@/components/ui/Accordion";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import type * as React from "react";
import { BotanicalGroupItemContainer } from "./BotanicalGroupItemContainer";
import type { IBotanicalGroup } from "../services/FamilyService";

interface BotanicalGroupPresenterProps {
	readonly botanicalGroups: IBotanicalGroup[];
	readonly isLoading: boolean;
	readonly error: Error | null;
	readonly isSuccess: boolean;
	readonly onFamilyClick: (familyId: string) => void;
}

export function BotanicalGroupPresenter({
	botanicalGroups,
	isLoading,
	error,
	isSuccess,
	onFamilyClick,
}: BotanicalGroupPresenterProps) {
	if (isLoading) {
		return (
			<LoadingSpinner
				size="lg"
				className="h-64"
				aria-label="Loading botanical groups"
			/>
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

	if (isSuccess && botanicalGroups.length === 0) {
		return (
			<div className="text-center py-8">
				<p className="text-muted-foreground">No botanical groups found.</p>
			</div>
		);
	}

	return (
		<div className="w-full max-w-2xl mx-auto min-h-[32rem] flex flex-col">
			<h1 className="text-3xl font-bold mb-6 text-center">Botanical Groups</h1>
			<Accordion type="multiple" className="w-full space-y-2">
				{botanicalGroups.map((group) => (
					<BotanicalGroupItemContainer
						key={group.botanical_group_id}
						group={group}
						onFamilyClick={onFamilyClick}
					/>
				))}
			</Accordion>
		</div>
	);
}
