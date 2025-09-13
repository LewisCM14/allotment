import type { VarietyList } from "../services/growGuideService";
import { Skeleton } from "../../../components/ui/Skeleton";
import { Leaf, Eye, EyeOff, Trash2, Search } from "lucide-react";
import { Input } from "../../../components/ui/Input";
import { Switch } from "../../../components/ui/Switch";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { useEffect, useState } from "react";

interface GrowGuideListPresenterProps {
	growGuides: VarietyList[];
	isLoading: boolean;
	isError: boolean;
}

export const GrowGuideListPresenter = ({
	growGuides,
	isLoading,
	isError,
}: GrowGuideListPresenterProps) => {
	const [searchTerm, setSearchTerm] = useState("");

	// Local copy so we can simulate delete before API endpoints exist
	const [localGuides, setLocalGuides] = useState<VarietyList[]>(growGuides);
	// Track public status locally keyed by id (initialised from props)
	const [publicMap, setPublicMap] = useState<Record<string, boolean>>({});
	// Single active guide id (wire to backend later)
	const [activeGuideId, setActiveGuideId] = useState<string | null>(null);

	// Sync local state when incoming list changes (e.g. refetch)
	useEffect(() => {
		setLocalGuides(growGuides);
		// build public map
		const map: Record<string, boolean> = {};
		growGuides.forEach(g => { map[g.variety_id] = g.is_public; });
		setPublicMap(map);
	}, [growGuides]);

	// Filter guides based on search term
	const filteredGuides = localGuides.filter((guide) =>
		guide.variety_name.toLowerCase().includes(searchTerm.toLowerCase()),
	);

	// Placeholder handlers (to be replaced with real mutations)
	const handleDelete = (id: string) => {
		if (window.confirm("Delete this grow guide? This cannot be undone.")) {
			setLocalGuides(prev => prev.filter(g => g.variety_id !== id));
			// TODO: Integrate deleteVariety mutation when API endpoint is ready
		}
	};

	const handleTogglePublic = (id: string) => {
		setPublicMap(prev => ({ ...prev, [id]: !prev[id] }));
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
					{Array.from({ length: 6 }).map((_, i) => (
						<div
							key={`skeleton-row-${i}`}
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
						<div className="space-y-2" role="list" aria-label="Grow guide list">
							{filteredGuides.map((guide) => {
								const isPublic = publicMap[guide.variety_id];
								const isActive = activeGuideId === guide.variety_id;
								return (
									<div
										key={guide.variety_id}
										role="listitem"
										className="flex items-center gap-4 p-3 border rounded-md bg-card hover:bg-accent/30 transition-colors"
									>
										{/* Delete Button */}
										<Button
											type="button"
											variant="destructive"
											size="icon"
											aria-label={`Delete ${guide.variety_name}`}
											onClick={() => handleDelete(guide.variety_id)}
											className="shrink-0 w-10 h-10"
										>
											<Trash2 className="h-4 w-4" />
										</Button>

										{/* Public / Private Toggle */}
										<Button
											type="button"
											variant={isPublic ? "secondary" : "outline"}
											size="icon"
											aria-pressed={isPublic}
											aria-label={`${isPublic ? "Make" : "Set"} ${guide.variety_name} ${isPublic ? "Private" : "Public"}`}
											onClick={() => handleTogglePublic(guide.variety_id)}
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
											<div className="flex items-center gap-2">
												<span className="font-medium truncate">
													{guide.variety_name}
												</span>
												<Badge variant="outline" className="hidden sm:inline">
													{guide.lifecycle.lifecycle_name}
												</Badge>
											</div>
											<p className="text-xs text-muted-foreground mt-0.5">
												Updated {new Date(guide.last_updated).toLocaleDateString()}
											</p>
										</div>

										{/* Active Toggle */}
										<div className="flex items-center gap-2 ml-auto">
											<span className="text-xs text-muted-foreground hidden sm:inline">Active</span>
											<Switch
												checked={isActive}
												onCheckedChange={(checked) => handleToggleActive(guide.variety_id, checked)}
												aria-label={`Set ${guide.variety_name} ${isActive ? "inactive" : "active"}`}
											/>
										</div>
									</div>
								);
							})}
						</div>
					)}
				</>
			)}
		</div>
	);
};
