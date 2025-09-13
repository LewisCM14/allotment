import type { VarietyList } from "../services/growGuideService";
import { Skeleton } from "@/components/ui/Skeleton";
import { Leaf, Eye, EyeOff, Trash2, Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useEffect, useState, useMemo } from "react";
import { useDeleteVariety } from "../hooks/useDeleteVariety";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/AlertDialog";

interface GrowGuideListPresenterProps {
	growGuides: VarietyList[];
	isLoading: boolean;
	isError: boolean;
	onSelect?: (varietyId: string) => void;
	selectedVarietyId?: string | null;
}

export const GrowGuideListPresenter = ({
	growGuides,
	isLoading,
	isError,
	onSelect,
	selectedVarietyId,
}: GrowGuideListPresenterProps) => {
	const [searchTerm, setSearchTerm] = useState("");

	// Local copy so we can simulate delete before API endpoints exist
	const [localGuides, setLocalGuides] = useState<VarietyList[]>(growGuides);
	// Track public status locally keyed by id (initialized from props)
	const [publicMap, setPublicMap] = useState<Record<string, boolean>>({});
	// Single active guide id (wire to backend later)
	const [activeGuideId, setActiveGuideId] = useState<string | null>(null);
	const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

	const { mutate: deleteVariety, isPending: isDeleting } = useDeleteVariety();

	// Sync local state when incoming list changes (e.g. refetch)
	useEffect(() => {
		setLocalGuides(growGuides);
		// build public map using for..of for lint compliance
		const map: Record<string, boolean> = {};
		for (const g of growGuides) {
			map[g.variety_id] = g.is_public;
		}
		setPublicMap(map);
	}, [growGuides]);

	// Filter guides based on search term
	const filteredGuides = useMemo(
		() =>
			localGuides.filter((guide) =>
				guide.variety_name.toLowerCase().includes(searchTerm.toLowerCase()),
			),
		[localGuides, searchTerm],
	);

	const groupedGuides = useMemo(() => {
		const groups: Record<string, VarietyList[]> = {};
		for (const g of filteredGuides) {
			const key = g.family.family_name;
			if (!groups[key]) {
				groups[key] = [];
			}
			groups[key].push(g);
		}
		return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
	}, [filteredGuides]);

	// Placeholder handlers (to be replaced with real mutations)
	const handleDelete = (id: string) => {
		// Optimistic UI removal after mutation success handled by refetch; keep local removal immediate for snappy feel
		deleteVariety(id, {
			onSuccess: () => {
				setLocalGuides((prev) => prev.filter((g) => g.variety_id !== id));
				setPendingDeleteId(null);
			},
			onError: () => {
				setPendingDeleteId(null); // close dialog; toast could be added later
			},
		});
	};

	const handleTogglePublic = (id: string) => {
		setPublicMap((prev) => ({ ...prev, [id]: !prev[id] }));
		// TODO: Integrate toggleVarietyPublic mutation when API endpoint is ready
	};

	const handleToggleActive = (id: string, checked: boolean) => {
		setActiveGuideId(checked ? id : null);
		// TODO: Integrate setActiveVariety endpoint (not yet implemented)
	};

	if (isLoading) {
		return (
			<div className="space-y-4">
				<Skeleton className="h-8 w-1/4" />
				<div className="space-y-2">
					{["a", "b", "c", "d", "e", "f"].map((id) => (
						<div
							key={`skeleton-row-${id}`}
							className="flex items-center gap-4 p-3 border rounded-md bg-card"
						>
							<Skeleton className="h-8 w-8 rounded" />
							<Skeleton className="h-8 w-8 rounded" />
							<div className="flex-1 space-y-2">
								<Skeleton className="h-4 w-1/3" />
								<Skeleton className="h-3 w-1/4" />
							</div>
							<Skeleton className="h-5 w-12 rounded" />
						</div>
					))}
				</div>
			</div>
		);
	}

	if (isError) {
		// Show same empty state style as when no guides (treat error generically for now)
		return (
			<div className="text-center py-10 space-y-4">
				<div className="mx-auto bg-primary w-16 h-16 rounded-full flex items-center justify-center">
					<Leaf className="h-8 w-8 text-primary-foreground" />
				</div>
				<p className="text-muted-foreground max-w-md mx-auto">
					We were unable to load your grow guides. Please refresh or try again
					later.
				</p>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{localGuides.length === 0 ? (
				<div className="text-center py-10 space-y-4">
					<div className="mx-auto bg-primary w-16 h-16 rounded-full flex items-center justify-center">
						<Leaf className="h-8 w-8 text-primary-foreground" />
					</div>
					<p className="text-muted-foreground max-w-md mx-auto">
						You don't have any grow guides yet. Click the "Add New Guide" button
						above to create your first guide and start tracking your plants.
					</p>
				</div>
			) : (
				<>
					<div className="relative">
						<Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search guides..."
							className="pl-10"
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
						/>
					</div>

					{filteredGuides.length === 0 ? (
						<div className="text-center py-10">
							<p className="text-muted-foreground">
								No grow guides found. Try a different search term.
							</p>
						</div>
					) : (
						<ul
							className="space-y-8"
							aria-label="Grow guide list grouped by family"
						>
							{groupedGuides.map(([familyName, guides]) => (
								<li key={familyName} className="space-y-2">
									<h3 className="text-sm font-semibold text-muted-foreground select-none capitalize">
										{familyName}
									</h3>
									<ul className="space-y-2">
										{guides.map((guide) => {
											const isPublic = publicMap[guide.variety_id];
											const isActive = activeGuideId === guide.variety_id;
											const isSelected = selectedVarietyId === guide.variety_id;
											return (
												<li key={guide.variety_id} className="list-none">
													<button
														type="button"
														className={`w-full text-left group flex items-center gap-4 p-3 border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background ${isSelected ? "bg-accent/60 border-primary" : "bg-card hover:bg-accent/30"}`}
														aria-pressed={isSelected}
														onClick={(e) => {
															// Prevent clicks on internal action buttons/switch from triggering selection
															const target = e.target as HTMLElement;
															if (target.closest("button, [role='switch']"))
																return;
															onSelect?.(guide.variety_id);
														}}
														onKeyDown={(e) => {
															if (e.key === "Enter" || e.key === " ") {
																e.preventDefault();
																onSelect?.(guide.variety_id);
															}
														}}
													>
														{/* Delete Button */}
														<AlertDialog
															open={pendingDeleteId === guide.variety_id}
															onOpenChange={(open: boolean) => {
																if (open) setPendingDeleteId(guide.variety_id);
																else if (pendingDeleteId === guide.variety_id)
																	setPendingDeleteId(null);
															}}
														>
															<AlertDialogTrigger asChild>
																<Button
																	type="button"
																	variant="destructive"
																	size="icon"
																	aria-label={`Delete ${guide.variety_name}`}
																	onClick={() =>
																		setPendingDeleteId(guide.variety_id)
																	}
																	className="shrink-0 w-10 h-10"
																	disabled={
																		isDeleting &&
																		pendingDeleteId === guide.variety_id
																	}
																>
																	<Trash2 className="h-4 w-4" />
																</Button>
															</AlertDialogTrigger>
															<AlertDialogContent>
																<AlertDialogHeader>
																	<AlertDialogTitle>
																		Delete Grow Guide
																	</AlertDialogTitle>
																	<AlertDialogDescription>
																		Are you sure you want to delete "
																		{guide.variety_name}"? This action is
																		permanent and cannot be undone.
																	</AlertDialogDescription>
																</AlertDialogHeader>
																<AlertDialogFooter>
																	<AlertDialogCancel disabled={isDeleting}>
																		Cancel
																	</AlertDialogCancel>
																	<AlertDialogAction
																		onClick={() =>
																			handleDelete(guide.variety_id)
																		}
																		disabled={isDeleting}
																	>
																		{isDeleting &&
																		pendingDeleteId === guide.variety_id
																			? "Deleting..."
																			: "Delete"}
																	</AlertDialogAction>
																</AlertDialogFooter>
															</AlertDialogContent>
														</AlertDialog>

														{/* Public / Private Toggle */}
														<Button
															type="button"
															variant={isPublic ? "secondary" : "outline"}
															size="icon"
															aria-pressed={isPublic}
															aria-label={`${isPublic ? "Make" : "Set"} ${guide.variety_name} ${isPublic ? "Private" : "Public"}`}
															onClick={() =>
																handleTogglePublic(guide.variety_id)
															}
															className="shrink-0 w-10 h-10"
														>
															{isPublic ? (
																<Eye className="h-4 w-4" />
															) : (
																<EyeOff className="h-4 w-4" />
															)}
														</Button>

														{/* Guide Name & Meta */}
														<div className="flex-1 min-w-0 pl-1">
															<div className="flex items-center gap-2 flex-wrap">
																<span className="font-medium truncate">
																	{guide.variety_name}
																</span>
																<Badge
																	variant="outline"
																	className="hidden sm:inline"
																>
																	{guide.lifecycle.lifecycle_name}
																</Badge>
															</div>
															<p className="text-xs text-muted-foreground mt-0.5">
																Updated{" "}
																{new Date(
																	guide.last_updated,
																).toLocaleDateString()}
															</p>
														</div>

														{/* Active Toggle */}
														<div className="flex items-center gap-2 ml-auto">
															<span className="text-xs text-muted-foreground hidden sm:inline">
																Active
															</span>
															<Switch
																checked={isActive}
																onCheckedChange={(checked) =>
																	handleToggleActive(guide.variety_id, checked)
																}
																aria-label={`Set ${guide.variety_name} ${isActive ? "inactive" : "active"}`}
															/>
														</div>
													</button>
												</li>
											);
										})}
									</ul>
								</li>
							))}
						</ul>
					)}
				</>
			)}
		</div>
	);
};
