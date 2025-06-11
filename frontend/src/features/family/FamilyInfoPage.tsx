import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getFamilyInfo, type IFamilyInfo } from "./FamilyService";
import { FamilyInfoPresenter } from "./FamilyInfoPresenter";
import axios from "axios";

export default function FamilyInfoPage() {
	const { familyId } = useParams<{ familyId: string }>();
	const [data, setData] = useState<IFamilyInfo | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<Error | null>(null);

	useEffect(() => {
		if (!familyId) return;
		const controller = new AbortController();
		setIsLoading(true);
		setError(null);

		getFamilyInfo(familyId, controller.signal)
			.then(setData)
			.catch((err) => {
				if (!axios.isCancel(err)) setError(err as Error);
			})
			.finally(() => setIsLoading(false));

		return () => controller.abort();
	}, [familyId]);

	return (
		<FamilyInfoPresenter data={data} isLoading={isLoading} error={error} />
	);
}
