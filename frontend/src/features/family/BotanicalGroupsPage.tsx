import axios from "axios";
import type * as React from "react";
import { useEffect, useState } from "react";
import { BotanicalGroupListPresenter } from "./BotanicalGroupListPresenter";
import type { IBotanicalGroup } from "./FamilyService";
import { getBotanicalGroups } from "./FamilyService";

export default function BotanicalGroupsPage() {
	const [botanicalGroups, setBotanicalGroups] = useState<IBotanicalGroup[]>([]);
	const [isLoading, setIsLoading] = useState<boolean>(true);
	const [error, setError] = useState<Error | null>(null);

	useEffect(() => {
		const controller = new AbortController();
		const signal = controller.signal;
		let caughtError: Error | null = null;

		async function fetchData() {
			try {
				setError(null);
				caughtError = null;
				const data = await getBotanicalGroups(signal);
				setBotanicalGroups(data);
			} catch (err) {
				if (axios.isCancel(err)) {
					if (err instanceof Error) caughtError = err;
				} else {
					setError(err as Error);
					caughtError = err as Error;
				}
			} finally {
				if (!axios.isCancel(caughtError)) {
					setIsLoading(false);
				}
			}
		}
		fetchData();

		return () => {
			controller.abort();
		};
	}, []);

	return (
		<BotanicalGroupListPresenter
			botanicalGroups={botanicalGroups}
			isLoading={isLoading}
			error={error}
		/>
	);
}
