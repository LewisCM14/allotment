import { PageLayout } from "../../../components/layouts/PageLayout";
import { GrowGuideListContainer } from "../components/GrowGuideListContainer";
import { Button } from "../../../components/ui/Button";
import { Plus } from "lucide-react";
import { useState, useEffect } from "react";
import { GrowGuideForm } from "../forms/GrowGuideForm";
import { useQueryClient } from "@tanstack/react-query";
import { growGuideService } from "../services/growGuideService";

// Keys reused across list + options
const USER_GUIDES_KEY = ["userGrowGuides"]; // must match useUserGrowGuides hook key
const OPTIONS_KEY = ["growGuideOptions"]; // must match useGrowGuideOptions hook key

const GrowGuides = () => {
	const [isFormOpen, setIsFormOpen] = useState(false);
	const queryClient = useQueryClient();

	// Prefetch options & user guides on mount so form opens instantly
	useEffect(() => {
		queryClient.prefetchQuery({
			queryKey: OPTIONS_KEY,
			queryFn: growGuideService.getGrowGuideOptions,
		});
		queryClient.prefetchQuery({
			queryKey: USER_GUIDES_KEY,
			queryFn: growGuideService.getUserGrowGuides,
		});
	}, [queryClient]);

	return (
		<PageLayout>
			<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
				<div>
					<h1 className="text-3xl font-bold tracking-tight">Grow Guides</h1>
					<p className="text-muted-foreground mt-1">
						Manage and explore your plant grow guides
					</p>
				</div>
				<Button onClick={() => setIsFormOpen(true)}>
					<Plus className="mr-2 h-4 w-4" />
					Add New Guide
				</Button>
			</div>
			<GrowGuideListContainer />

			{/* Add new grow guide form dialog */}
			<GrowGuideForm isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} />
		</PageLayout>
	);
};
export default GrowGuides;
