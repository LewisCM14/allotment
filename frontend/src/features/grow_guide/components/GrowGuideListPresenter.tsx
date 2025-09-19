import type { VarietyList } from "../services/growGuideService";
import { Skeleton } from "@/components/ui/Skeleton";
import { Leaf, Eye, EyeOff, Trash2, Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useEffect, useMemo, useState } from "react";
import { useDeleteVariety } from "../hooks/useDeleteVariety";
import { useToggleVarietyPublic } from "../hooks/useToggleVarietyPublic";
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

interface Props {
	growGuides: VarietyList[];
	isLoading: boolean;
	isError: boolean;
	onSelect?: (id: string) => void;
	selectedVarietyId?: string | null;
}

export const GrowGuideListPresenter = ({
	growGuides,
	isLoading,
	isError,
	onSelect,
	selectedVarietyId,
}: Props) => {
	const [search, setSearch] = useState("");
	const [localGuides, setLocalGuides] = useState<VarietyList[]>(growGuides);
	const [publicMap, setPublicMap] = useState<Record<string, boolean>>({});
	const [activeGuideId, setActiveGuideId] = useState<string | null>(null);
	const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
	const [suppressNextSelect, setSuppressNextSelect] = useState(false);

	const { mutate: deleteVariety, isPending: isDeleting } = useDeleteVariety();
	const { mutate: togglePublicMutation, isPending: isToggling } =
		useToggleVarietyPublic();

	useEffect(() => {
		setLocalGuides(growGuides);
		const map: Record<string, boolean> = {};
		for (const g of growGuides) map[g.variety_id] = g.is_public;
		setPublicMap(map);
	}, [growGuides]);

	const filtered = useMemo(
		() =>
			localGuides.filter((g) =>
				g.variety_name.toLowerCase().includes(search.toLowerCase()),
			),
		[localGuides, search],
	);

	const grouped = useMemo(() => {
		const groups: Record<string, VarietyList[]> = {};
		for (const g of filtered) {
			const key = g.family?.family_name || "Unknown Family";
			if (!groups[key]) groups[key] = [];
			groups[key].push(g);
		}
		return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
	}, [filtered]);

	const handleDelete = (id: string) => {
		deleteVariety(id, {
			onSuccess: () => {
				setLocalGuides((prev) => prev.filter((g) => g.variety_id !== id));
				setPendingDeleteId(null);
			},
			onError: () => setPendingDeleteId(null),
		});
	};

	const togglePublic = (id: string) => {
		setPublicMap((prev) => ({ ...prev, [id]: !prev[id] })); // optimistic local state
		const current = publicMap[id];
		togglePublicMutation(
			{ varietyId: id, currentIsPublic: current },
			{
				onError: () => {
					// rollback local map on error
					setPublicMap((prev) => ({ ...prev, [id]: current }));
				},
			},
		);
	};

	const toggleActive = (id: string, checked: boolean) => {
		setActiveGuideId(checked ? id : null);
	};

	if (isLoading) {
		return (
			<div className="space-y-4">
				<Skeleton className="h-8 w-1/4" />
				<div className="space-y-2">
					{["a", "b", "c", "d", "e", "f"].map((id) => (
						<div
							key={id}
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
							value={search}
							onChange={(e) => setSearch(e.target.value)}
						/>
					</div>
					{filtered.length === 0 ? (
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
							{grouped.map(([family, guides]) => (
								<li key={family} className="space-y-2">
									<h3 className="text-sm font-semibold text-muted-foreground select-none capitalize">
										{family}
									</h3>
									<ul className="space-y-2">
										{guides.map((g) => {
											const isPublic = publicMap[g.variety_id] ?? g.is_public;
											const isActive = activeGuideId === g.variety_id;
											const isSelected = selectedVarietyId === g.variety_id;
											return (
												<li key={g.variety_id} className="list-none">
													<div
														className={`w-full flex items-center gap-4 p-3 border rounded-md transition-colors ${isSelected ? "bg-accent/60 border-primary" : "bg-card hover:bg-accent/30"} cursor-pointer`}
														data-row-container
													>
														{/* Delete */}
														<AlertDialog
															open={pendingDeleteId === g.variety_id}
															onOpenChange={(open: boolean) => {
																if (open) setPendingDeleteId(g.variety_id);
																else if (pendingDeleteId === g.variety_id)
																	setPendingDeleteId(null);
															}}
														>
															<AlertDialogTrigger asChild>
																<Button
																	type="button"
																	variant="destructive"
																	size="icon"
																	aria-label={`Delete ${g.variety_name}`}
																	data-row-action
																	onClick={(
																		e: React.MouseEvent<HTMLButtonElement>,
																	) => {
																		e.stopPropagation();
																		setPendingDeleteId(g.variety_id);
																	}}
																	disabled={
																		isDeleting &&
																		pendingDeleteId === g.variety_id
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
																		{g.variety_name}"? This action is permanent
																		and cannot be undone.
																	</AlertDialogDescription>
																</AlertDialogHeader>
																<AlertDialogFooter>
																	<AlertDialogCancel
																		data-row-action
																		disabled={isDeleting}
																		onClick={(
																			e: React.MouseEvent<HTMLButtonElement>,
																		) => {
																			e.stopPropagation();
																			setSuppressNextSelect(true);
																		}}
																	>
																		Cancel
																	</AlertDialogCancel>
																	<AlertDialogAction
																		data-row-action
																		disabled={isDeleting}
																		onClick={() => handleDelete(g.variety_id)}
																	>
																		{isDeleting &&
																		pendingDeleteId === g.variety_id
																			? "Deleting..."
																			: "Delete"}
																	</AlertDialogAction>
																</AlertDialogFooter>
															</AlertDialogContent>
														</AlertDialog>

														{/* Visibility/public toggle */}
														<Button
															type="button"
															variant={isPublic ? "secondary" : "outline"}
															size="icon"
															aria-pressed={isPublic}
															aria-label={`${isPublic ? "Make" : "Set"} ${g.variety_name} ${isPublic ? "Private" : "Public"}`}
															data-row-action
															onClick={(e) => {
																e.stopPropagation();
																if (isToggling) return;
																togglePublic(g.variety_id);
															}}
														>
															{isPublic ? (
																<Eye className="h-4 w-4" />
															) : (
																<EyeOff className="h-4 w-4" />
															)}
														</Button>

														{/* Main selectable content */}
														<button
															type="button"
															className="flex-1 text-left pl-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded cursor-pointer"
															aria-pressed={isSelected}
															data-row-select
															onClick={() => {
																if (suppressNextSelect) {
																	setSuppressNextSelect(false);
																	return;
																}
																onSelect?.(g.variety_id);
															}}
														>
															<div className="flex items-center gap-2 flex-wrap">
																<span className="font-medium truncate">
																	{g.variety_name}
																</span>
																<Badge
																	variant="outline"
																	className="hidden sm:inline"
																>
																	{g.lifecycle.lifecycle_name}
																</Badge>
															</div>
															<p className="text-xs text-muted-foreground mt-0.5">
																Updated{" "}
																{new Date(g.last_updated).toLocaleDateString()}
															</p>
														</button>

														{/* Active toggle */}
														<div
															className="flex items-center gap-2 ml-auto"
															data-row-action
														>
															<span className="text-xs text-muted-foreground hidden sm:inline">
																Active
															</span>
															<Switch
																checked={isActive}
																onCheckedChange={(checked: boolean) =>
																	toggleActive(g.variety_id, checked)
																}
																aria-label={`Set ${g.variety_name} active`}
																className="cursor-pointer"
															/>
														</div>
													</div>
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
