import { useParams } from "react-router-dom";
import { FamilyInfoPresenter } from "./FamilyInfoPresenter";
import { useFamilyInfo } from "./hooks/useFamilyInfo";

export default function FamilyInfoPage() {
	const { familyId } = useParams<{ familyId: string }>();
	const { data, isLoading, error, isSuccess } = useFamilyInfo(familyId);

	return (
		<FamilyInfoPresenter
			data={data || null}
			isLoading={isLoading}
			error={error || null}
			isSuccess={isSuccess}
		/>
	);
}
