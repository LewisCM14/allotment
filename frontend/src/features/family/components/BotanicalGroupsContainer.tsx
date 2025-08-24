import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BotanicalGroupPresenter } from "./BotanicalGroupPresenter";
import { useBotanicalGroups } from "../hooks/useBotanicalGroups";

export default function BotanicalGroupsContainer() {
	const navigate = useNavigate();
	const {
		data: botanicalGroups = [],
		isLoading,
		error,
		isSuccess,
	} = useBotanicalGroups();

	useEffect(() => {
		const main = document.querySelector("main.flex-1");
		if (main && typeof main.scrollTo === "function") {
			main.scrollTo({ top: 0, left: 0, behavior: "smooth" });
		} else if (typeof window.scrollTo === "function") {
			window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
		}
	}, []);

	const handleFamilyNavigation = (familyId: string) => {
		navigate(`/family/${familyId}`);
	};

	return (
		<BotanicalGroupPresenter
			botanicalGroups={botanicalGroups}
			isLoading={isLoading}
			error={error || null}
			isSuccess={isSuccess}
			onFamilyClick={handleFamilyNavigation}
		/>
	);
}
