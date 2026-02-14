import { PageLayout } from "@/components/layouts/PageLayout";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SearchField } from "@/components/ui/SearchField";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/Accordion";
// We prefer a simpler list look here to mirror the Botanical Groups presentation
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { lazyToast } from "@/utils/lazyToast";
import { useMemo, useState, type ReactNode, lazy, Suspense } from "react";
import {
	growGuideService,
	type VarietyList,
} from "../services/growGuideService";
import { useQueryClient } from "@tanstack/react-query";
import { usePublicGrowGuides } from "../hooks/usePublicGrowGuides";
import { useAuth } from "@/store/auth/AuthContext";

const GrowGuideForm = lazy(() =>
	import("../forms/GrowGuideForm").then((module) => ({
		default: module.GrowGuideForm,
	})),
);

const groupGuidesByFamily = (guides: VarietyList[]) => {
	const groups: Record<string, VarietyList[]> = {};
	for (const g of guides) {
		const key = g.family?.family_name || "Unknown Family";
		if (!groups[key]) {
			groups[key] = [];
		}
		groups[key].push(g);
	}
	const entries = Object.entries(groups);
	entries.sort(([a], [b]) => a.localeCompare(b));
	return entries.map(
		([family, items]) =>
			[
				family,
				// avoid mutating original array
				[...items].sort((a, b) => a.variety_name.localeCompare(b.variety_name)),
			] as const,
	);
};

const PublicGrowGuides = () => {
	const queryClient = useQueryClient();
	const { isAuthenticated } = useAuth();
	const { data, isLoading, isError } = usePublicGrowGuides();
	const [search, setSearch] = useState("");
	const [viewOpen, setViewOpen] = useState(false);
	const [viewVarietyId, setViewVarietyId] = useState<string | null>(null);

	const filtered = useMemo(() => {
		const guides = data ?? [];
		if (!search.trim()) return guides;
		const term = search.toLowerCase();
		return guides.filter((g) => g.variety_name.toLowerCase().includes(term));
	}, [data, search]);

	const grouped = useMemo(() => groupGuidesByFamily(filtered), [filtered]);

	const handleCopy = async (varietyId: string) => {
		try {
			if (!isAuthenticated) {
				lazyToast.info("Please log in to copy a guide to your account.");
				return;
			}
			const created = await growGuideService.copyPublicVariety(varietyId);
			lazyToast.success(`Copied "${created.variety_name}" to your guides.`);
			// Invalidate user guides so it appears in their list on next visit
			await queryClient.invalidateQueries({ queryKey: ["userGrowGuides"] });
			return created;
		} catch (e) {
			const message = e instanceof Error ? e.message : "Failed to copy guide.";
			lazyToast.error(message);
		}
	};

	const handleOpenFromPublic = (publicVarietyId: string) => {
		// Open the form in read-only mode for viewing a public guide
		if (!isAuthenticated) {
			lazyToast.info("Please log in to view grow guide details.");
			return;
		}
		setViewVarietyId(publicVarietyId);
		setViewOpen(true);
	};

	// Extract nested ternary into an independent statement for readability
	let content: ReactNode;
	if (isLoading) {
		content = <LoadingSpinner size="lg" label="Loading public grow guides" />;
	} else if (isError) {
		content = (
			<div className="text-center py-10">
				<p className="text-muted-foreground">
					We couldn't load public guides right now. Please try again later.
				</p>
			</div>
		);
	} else {
		content = (
			<section
				className="space-y-6"
				aria-label="Public grow guides grouped by family"
			>
				<SearchField
					value={search}
					onChange={setSearch}
					placeholder="Search guides..."
					ariaLabel="Search public grow guides"
				/>

				{filtered.length === 0 && (data?.length ?? 0) > 0 ? (
					<div className="text-center py-10">
						<p className="text-muted-foreground">
							No public guides found. Try a different search term.
						</p>
					</div>
				) : null}

				<Accordion type="multiple" className="w-full space-y-2">
					{grouped.map(([family, guides]) => (
						<AccordionItem key={family} value={family}>
							<AccordionTrigger className="cursor-pointer">
								<h2 className="text-xl font-semibold text-card-foreground capitalize">
									{family}
								</h2>
							</AccordionTrigger>
							<AccordionContent>
								<ul className="space-y-2">
									{guides.map((g) => (
										<li key={g.variety_id} className="list-none">
											<div className="w-full flex items-center gap-2 sm:gap-4 p-2 sm:p-3 border rounded-md bg-card hover:bg-accent/30 transition-colors">
												<button
													type="button"
													className="min-w-0 flex-1 text-left pl-0.5 sm:pl-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded cursor-pointer"
													onClick={() => handleOpenFromPublic(g.variety_id)}
												>
													<p className="text-xs sm:text-base font-medium truncate pr-1 sm:pr-2 text-card-foreground">
														{g.variety_name}
													</p>
													<div className="flex items-center gap-1 sm:gap-2 flex-wrap">
														<Badge
															variant="outline"
															className="text-[9px] sm:text-xs px-1 py-0 sm:px-2 sm:py-0.5"
														>
															{g.lifecycle.lifecycle_name}
														</Badge>
														<p className="text-[9px] sm:text-xs text-muted-foreground">
															Updated{" "}
															{new Date(g.last_updated).toLocaleDateString()}
														</p>
													</div>
												</button>
												<Button
													variant="default"
													size="sm"
													className="text-white"
													onClick={() => handleCopy(g.variety_id)}
												>
													Use this guide
												</Button>
											</div>
										</li>
									))}
								</ul>
							</AccordionContent>
						</AccordionItem>
					))}
				</Accordion>

				{/* View-only form modal */}
				<Suspense fallback={<LoadingSpinner />}>
					<GrowGuideForm
						isOpen={viewOpen}
						onClose={() => setViewOpen(false)}
						mode="view"
						varietyId={viewVarietyId}
					/>
				</Suspense>
				{data?.length === 0 && (
					<p className="text-muted-foreground">
						No public guides available yet.
					</p>
				)}
			</section>
		);
	}

	return (
		<PageLayout>
			<div className="mb-8">
				<h1 className="text-3xl font-bold tracking-tight">
					Public Grow Guides
				</h1>
				<p className="text-muted-foreground mt-1">
					Browse community grow guides by family and take a copy of the ones you
					want to use.
				</p>
			</div>
			{content}
		</PageLayout>
	);
};

export default PublicGrowGuides;

export { groupGuidesByFamily };
