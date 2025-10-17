import { PageLayout } from "../../../components/layouts/PageLayout";
import { GrowGuideListContainer } from "../components/GrowGuideListContainer";
import { Button } from "../../../components/ui/Button";
import { Plus } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { GrowGuideForm } from "../forms/GrowGuideForm";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { growGuideService } from "../services/growGuideService";
import { growGuideQueryKey } from "../hooks/useGrowGuide";
import { useUserGrowGuides } from "../hooks/useUserGrowGuides";

// Keys reused across list + options
const USER_GUIDES_KEY = ["userGrowGuides"]; // must match useUserGrowGuides hook key
const OPTIONS_KEY = ["growGuideOptions"]; // must match useGrowGuideOptions hook key

const GrowGuides = () => {
	const [isFormOpen, setIsFormOpen] = useState(false);
	const [selectedVarietyId, setSelectedVarietyId] = useState<string | null>(
		null,
	);
	// Mode: create (new guide) or edit (existing guide)
	const [mode, setMode] = useState<"create" | "edit">("create");
	const queryClient = useQueryClient();
	const { data: growGuides, isLoading } = useUserGrowGuides();

	const hasGuides =
		!isLoading && Array.isArray(growGuides) && growGuides.length > 0;

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

	const handleAddNew = () => {
		setSelectedVarietyId(null);
		setMode("create");
		setIsFormOpen(true);
	};

	const handleSelectGuide = useCallback(
		(varietyId: string) => {
			setSelectedVarietyId(varietyId);
			setMode("edit");
			setIsFormOpen(true);
			void queryClient
				.ensureQueryData({
					queryKey: growGuideQueryKey(varietyId),
					queryFn: () => growGuideService.getGrowGuide(varietyId),
				})
				.catch((error) => {
					const message =
						error instanceof Error
							? error.message
							: "Failed to load grow guide";
					toast.error(message);
				});
		},
		[queryClient],
	);

	return (
		<PageLayout>
			{hasGuides && (
				<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
					<div>
						<h1 className="text-3xl font-bold tracking-tight">Grow Guides</h1>
						<p className="text-muted-foreground mt-1">
							Manage and explore your plant grow guides
						</p>
					</div>
					<Button onClick={handleAddNew}>
						<Plus className="mr-2 h-4 w-4" />
						Add New Guide
					</Button>
				</div>
			)}
			<GrowGuideListContainer
				onSelect={handleSelectGuide}
				selectedVarietyId={selectedVarietyId}
				onAddNew={handleAddNew}
			/>

			{/* Grow guide form handles create, view, edit based on props */}
			<GrowGuideForm
				isOpen={isFormOpen}
				onClose={() => setIsFormOpen(false)}
				varietyId={selectedVarietyId ?? undefined}
				mode={mode}
			/>
		</PageLayout>
	);
};
export default GrowGuides;
