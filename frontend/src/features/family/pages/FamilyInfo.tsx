import { PageLayout } from "@/components/layouts/PageLayout";
import { useParams } from "react-router-dom";
import { useEffect } from "react";
import { FamilyInfoPresenter } from "../components/FamilyInfoPresenter";
import { useFamilyInfo } from "../hooks/useFamilyInfo";

export default function FamilyInfoPage() {
	const { familyId } = useParams<{ familyId: string }>();
	const { data, isLoading, error, isSuccess } = useFamilyInfo(familyId);

	// biome-ignore lint/correctness/useExhaustiveDependencies: scroll-to-top should run on route change
	useEffect(() => {
		const main = document.querySelector("main.flex-1");
		if (main && typeof main.scrollTo === "function") {
			main.scrollTo({ top: 0, left: 0, behavior: "smooth" });
		} else if (typeof window.scrollTo === "function") {
			window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
		}
	}, [familyId]);

	return (
		<PageLayout>
			<FamilyInfoPresenter
				data={data || null}
				isLoading={isLoading}
				error={error || null}
				isSuccess={isSuccess}
			/>
		</PageLayout>
	);
}
