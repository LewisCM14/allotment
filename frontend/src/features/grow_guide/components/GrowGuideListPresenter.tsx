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
import { useToggleActiveVariety } from "../hooks/useToggleActiveVariety";
import { GrowGuideEmptyState } from "./GrowGuideEmptyState";
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
	onAddNew?: () => void;
}

export const GrowGuideListPresenter = ({
	growGuides,
	isLoading,
	isError,
	onSelect,
	selectedVarietyId,
	onAddNew,
}: Props) => {
	const [search, setSearch] = useState("");
	const [localGuides, setLocalGuides] = useState<VarietyList[]>(growGuides);
	const [publicMap, setPublicMap] = useState<Record<string, boolean>>({});
	const [activeMap, setActiveMap] = useState<Record<string, boolean>>({});
	const [pendingActiveId, setPendingActiveId] = useState<string | null>(null);
	const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
	const [suppressNextSelect, setSuppressNextSelect] = useState(false);

	const { mutate: deleteVariety, isPending: isDeleting } = useDeleteVariety();
	const { mutate: togglePublicMutation, isPending: isTogglingPublic } =
		useToggleVarietyPublic();
	const { mutate: toggleActiveMutation, isPending: isTogglingActive } =
		useToggleActiveVariety();

	const openDeleteDialog = (id: string) => setPendingDeleteId(id);
	const closeDeleteDialog = () => setPendingDeleteId(null);

	const handleDeleteSuccess = (id: string) => {
		setLocalGuides((prev) => prev.filter((g) => g.variety_id !== id));
		setPublicMap((prev) => {
			const { [id]: _removed, ...rest } = prev;
			return rest;
		});
		setActiveMap((prev) => {
			const { [id]: _removed, ...rest } = prev;
			return rest;
		});
		setPendingDeleteId(null);
	};

	const handleDeleteError = () => setPendingDeleteId(null);

	const handleToggleError = (id: string, current: boolean) => {
		setPublicMap((prev) => ({ ...prev, [id]: current }));
	};

	useEffect(() => {
		setLocalGuides(growGuides);
		const map: Record<string, boolean> = {};
		const activeStatus: Record<string, boolean> = {};
		for (const g of growGuides) {
			map[g.variety_id] = g.is_public;
			activeStatus[g.variety_id] = g.is_active;
		}
		setPublicMap(map);
		setActiveMap(activeStatus);
		setPendingActiveId(null);
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
			onSuccess: () => handleDeleteSuccess(id),
			onError: handleDeleteError,
		});
	};

	const togglePublic = (id: string) => {
		setPublicMap((prev) => ({ ...prev, [id]: !prev[id] })); // optimistic local state
		const current = publicMap[id];
		togglePublicMutation(
			{ varietyId: id, currentIsPublic: current },
			{
				onError: () => handleToggleError(id, current),
			},
		);
	};

	const toggleActive = (id: string, checked: boolean) => {
		const previousState = { ...activeMap };
		// Optimistic update: only update this specific item
		setActiveMap((prev) => ({ ...prev, [id]: checked }));
		setPendingActiveId(id);
		toggleActiveMutation(
			{ varietyId: id, makeActive: checked },
			{
				onError: () => setActiveMap(previousState),
				onSettled: () =>
					setPendingActiveId((current) => (current === id ? null : current)),
			},
		);
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
				<GrowGuideEmptyState
					onAddNew={() => {
						onAddNew?.();
					}}
				/>
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
											const isActive = activeMap[g.variety_id] ?? g.is_active;
											const isSelected = selectedVarietyId === g.variety_id;
											return (
												<li key={g.variety_id} className="list-none">
													<div
														className={`w-full flex items-center gap-2 sm:gap-4 p-2 sm:p-3 border rounded-md transition-colors ${isSelected ? "bg-accent/60 border-primary" : "bg-card hover:bg-accent/30"} cursor-pointer`}
														data-row-container
													>
														{/* Delete */}
														<AlertDialog
															open={pendingDeleteId === g.variety_id}
															onOpenChange={(open: boolean) =>
																open
																	? openDeleteDialog(g.variety_id)
																	: closeDeleteDialog()
															}
														>
															<AlertDialogTrigger asChild>
																<Button
																	type="button"
																	variant="destructive"
																	size="icon"
																	aria-label={`Delete ${g.variety_name}`}
																	data-row-action
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
																if (isTogglingPublic) return;
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
															className="flex-1 text-left pl-0.5 sm:pl-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded cursor-pointer min-w-0"
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
															<div className="space-y-0.5 sm:space-y-1">
																<div className="text-xs sm:text-base font-medium truncate pr-1 sm:pr-2">
																	{g.variety_name}
																</div>
																<div className="flex items-center gap-1 sm:gap-2 flex-wrap">
																	<Badge
																		variant="outline"
																		className="text-[9px] sm:text-xs px-1 py-0 sm:px-2 sm:py-0.5"
																	>
																		{g.lifecycle.lifecycle_name}
																	</Badge>
																	{isActive && (
																		<Badge
																			variant="default"
																			className="text-[9px] sm:text-xs uppercase px-1 py-0 sm:px-2 sm:py-0.5"
																		>
																			Active
																		</Badge>
																	)}
																</div>
																<p className="text-[9px] sm:text-xs text-muted-foreground">
																	Updated{" "}
																	{new Date(
																		g.last_updated,
																	).toLocaleDateString()}
																</p>
															</div>
														</button>

														{/* Active toggle */}
														<div
															className="flex items-center gap-1.5 sm:gap-2 ml-auto self-center"
															data-row-action
														>
															<span className="text-[9px] sm:text-xs text-muted-foreground hidden sm:inline">
																Active
															</span>
															<Switch
																checked={isActive}
																onCheckedChange={(checked: boolean) =>
																	toggleActive(g.variety_id, checked)
																}
																disabled={
																	isTogglingActive &&
																	pendingActiveId === g.variety_id
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
