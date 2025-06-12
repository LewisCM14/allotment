import type * as React from "react";
import { BotanicalGroupListPresenter } from "./BotanicalGroupListPresenter";
import { useBotanicalGroups } from "./hooks/useBotanicalGroups";

export default function BotanicalGroupsPage() {
	const {
		data: botanicalGroups = [],
		isLoading,
		error,
		isSuccess,
	} = useBotanicalGroups();

	return (
		<BotanicalGroupListPresenter
			botanicalGroups={botanicalGroups}
			isLoading={isLoading}
			error={error || null}
			isSuccess={isSuccess}
		/>
	);
}
