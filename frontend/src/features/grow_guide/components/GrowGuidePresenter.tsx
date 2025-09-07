import { Button } from "@/components/ui/Button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Edit, Eye, Globe, Lock, Plus, Trash2, Loader2 } from "lucide-react";
import type { VarietyListRead, VarietyOptionsRead } from "../types/growGuideTypes";
import VarietyForm from "./VarietyForm";
import type { CreateVarietyFormData, UpdateVarietyFormData } from "../schemas/varietySchemas";

interface GrowGuidePresenterProps {
	readonly varieties: VarietyListRead[];
	readonly options?: VarietyOptionsRead;
	readonly isLoading: boolean;
	readonly error?: string;
	readonly isFormOpen: boolean;
	readonly editingVariety?: VarietyListRead;
	readonly isSubmitting: boolean;
	readonly formError?: string;
	readonly onCreateNew: () => void;
	readonly onEdit: (variety: VarietyListRead) => void;
	readonly onView: (variety: VarietyListRead) => void;
	readonly onDelete: (varietyId: string) => void;
	readonly onTogglePublic: (varietyId: string) => void;
	readonly onFormClose: () => void;
	readonly onFormSubmit: (data: CreateVarietyFormData | UpdateVarietyFormData) => void;
}

export default function GrowGuidePresenter({
	varieties,
	options,
	isLoading,
	error,
	isFormOpen,
	editingVariety,
	isSubmitting,
	formError,
	onCreateNew,
	onEdit,
	onView,
	onDelete,
	onTogglePublic,
	onFormClose,
	onFormSubmit,
}: GrowGuidePresenterProps) {
	if (isLoading) {
		return (
			<div className="space-y-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold">Grow Guides</h1>
						<p className="text-muted-foreground">
							Manage your plant growing guides and schedules
						</p>
					</div>
					<Button disabled>
						<Plus className="h-4 w-4 mr-2" />
						New Guide
					</Button>
				</div>
				<div className="flex items-center justify-center py-12">
					<Loader2 className="h-8 w-8 animate-spin" />
					<span className="ml-2">Loading your grow guides...</span>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="space-y-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold">Grow Guides</h1>
						<p className="text-muted-foreground">
							Manage your plant growing guides and schedules
						</p>
					</div>
					<Button onClick={onCreateNew}>
						<Plus className="h-4 w-4 mr-2" />
						New Guide
					</Button>
				</div>
				<Card>
					<CardContent className="py-8">
						<div className="text-center">
							<h3 className="text-lg font-semibold text-destructive mb-2">
								Failed to load grow guides
							</h3>
							<p className="text-muted-foreground">{error}</p>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold">Grow Guides</h1>
					<p className="text-muted-foreground">
						Manage your plant growing guides and schedules
					</p>
				</div>
				<Button onClick={onCreateNew}>
					<Plus className="h-4 w-4 mr-2" />
					New Guide
				</Button>
			</div>

			{options && (
				<Card>
					<CardHeader>
						<CardTitle className="text-lg">Available Options</CardTitle>
						<CardDescription>
							Current database contains options for creating grow guides
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
							<div>
								<span className="font-medium">Families:</span>
								<p className="text-muted-foreground">{options.families.length} types</p>
							</div>
							<div>
								<span className="font-medium">Lifecycles:</span>
								<p className="text-muted-foreground">{options.lifecycles.length} types</p>
							</div>
							<div>
								<span className="font-medium">Conditions:</span>
								<p className="text-muted-foreground">{options.planting_conditions.length} types</p>
							</div>
							<div>
								<span className="font-medium">Frequencies:</span>
								<p className="text-muted-foreground">{options.frequencies.length} types</p>
							</div>
							<div>
								<span className="font-medium">Weeks:</span>
								<p className="text-muted-foreground">{options.weeks.length} weeks</p>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{varieties.length === 0 ? (
				<Card>
					<CardContent className="py-12">
						<div className="text-center">
							<h3 className="text-lg font-semibold mb-2">No grow guides yet</h3>
							<p className="text-muted-foreground mb-4">
								Create your first grow guide to start planning your garden
							</p>
							<Button onClick={onCreateNew}>
								<Plus className="h-4 w-4 mr-2" />
								Create Your First Guide
							</Button>
						</div>
					</CardContent>
				</Card>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{varieties.map((variety) => (
						<Card key={variety.variety_id} className="hover:shadow-md transition-shadow">
							<CardHeader className="pb-3">
								<div className="flex items-start justify-between">
									<div className="flex-1">
										<CardTitle className="text-lg">{variety.variety_name}</CardTitle>
										<CardDescription className="flex items-center gap-2">
											{variety.lifecycle.lifecycle_name}
											{variety.is_public ? (
												<Badge variant="secondary" className="text-xs">
													<Globe className="h-3 w-3 mr-1" />
													Public
												</Badge>
											) : (
												<Badge variant="outline" className="text-xs">
													<Lock className="h-3 w-3 mr-1" />
													Private
												</Badge>
											)}
										</CardDescription>
									</div>
								</div>
							</CardHeader>
							<CardContent className="pt-0">
								<div className="space-y-2 text-sm text-muted-foreground mb-4">
									<p>Last updated: {new Date(variety.last_updated).toLocaleDateString()}</p>
								</div>
								<div className="flex items-center gap-2">
									<Button
										variant="outline"
										size="sm"
										onClick={() => onView(variety)}
										className="flex-1"
									>
										<Eye className="h-4 w-4 mr-1" />
										View
									</Button>
									<Button
										variant="outline"
										size="sm"
										onClick={() => onEdit(variety)}
									>
										<Edit className="h-4 w-4" />
									</Button>
									<Button
										variant="outline"
										size="sm"
										onClick={() => onTogglePublic(variety.variety_id)}
									>
										{variety.is_public ? <Lock className="h-4 w-4" /> : <Globe className="h-4 w-4" />}
									</Button>
									<Button
										variant="outline"
										size="sm"
										onClick={() => onDelete(variety.variety_id)}
										className="text-destructive hover:text-destructive"
									>
										<Trash2 className="h-4 w-4" />
									</Button>
								</div>
							</CardContent>
						</Card>
					))}
				</div>
			)}

			<VarietyForm
				isOpen={isFormOpen}
				onClose={onFormClose}
				onSubmit={onFormSubmit}
				variety={editingVariety ? {
					variety_id: editingVariety.variety_id,
					variety_name: editingVariety.variety_name,
					owner_user_id: "", // Not needed for form
					family: { family_id: "", family_name: "", botanical_group_id: "" }, // Will be populated from API
					lifecycle: editingVariety.lifecycle,
					planting_conditions: { planting_condition_id: "", planting_condition: "" }, // Will be populated from API
					sow_week_start_id: "",
					sow_week_end_id: "",
					soil_ph: undefined,
					plant_depth_cm: undefined,
					plant_space_cm: undefined,
					water_frequency: undefined,
					high_temp_water_frequency: undefined,
					harvest_week_start_id: undefined,
					harvest_week_end_id: undefined,
					is_public: editingVariety.is_public,
					last_updated: editingVariety.last_updated,
					water_days: [],
				} : undefined}
				isLoading={isSubmitting}
				error={formError}
			/>
		</div>
	);
}
