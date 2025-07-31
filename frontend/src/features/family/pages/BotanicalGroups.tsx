import { PageLayout } from "@/components/layouts/PageLayout";
import type * as React from "react";
import { BotanicalGroupListPresenter } from "../components/BotanicalGroupListPresenter";
import { useBotanicalGroups } from "../hooks/useBotanicalGroups";

export default function BotanicalGroupsPage() {
	const {
		data: botanicalGroups = [],
		isLoading,
		error,
		isSuccess,
	} = useBotanicalGroups();

	return (
		<PageLayout>
			<BotanicalGroupListPresenter
				botanicalGroups={botanicalGroups}
				isLoading={isLoading}
				error={error || null}
				isSuccess={isSuccess}
			/>
		</PageLayout>
	);
}
