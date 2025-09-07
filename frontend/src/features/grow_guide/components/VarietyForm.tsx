import { FormError } from "@/components/FormError";
import { Button } from "@/components/ui/Button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/Select";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Save, X } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { useVarietyOptions } from "../hooks/useGrowGuide";
import {
	createVarietySchema,
	updateVarietySchema,
	type CreateVarietyFormData,
	type UpdateVarietyFormData,
} from "../schemas/varietySchemas";
import type { VarietyRead } from "../types/growGuideTypes";

interface VarietyFormProps {
	readonly isOpen: boolean;
	readonly onClose: () => void;
	readonly onSubmit: (data: CreateVarietyFormData | UpdateVarietyFormData) => void;
	readonly variety?: VarietyRead;
	readonly isLoading?: boolean;
	readonly error?: string;
}

export default function VarietyForm({
	isOpen,
	onClose,
	onSubmit,
	variety,
	isLoading = false,
	error,
}: VarietyFormProps) {
	const isEditing = !!variety;
	const { data: options, isLoading: optionsLoading } = useVarietyOptions();

	const {
		register,
		handleSubmit,
		control,
		reset,
		formState: { errors },
	} = useForm<CreateVarietyFormData | UpdateVarietyFormData>({
		resolver: zodResolver(isEditing ? updateVarietySchema : createVarietySchema),
		defaultValues: isEditing
			? {
					variety_name: variety.variety_name,
					family_id: variety.family.family_id,
					lifecycle_id: variety.lifecycle.lifecycle_id,
					sow_week_start_id: variety.sow_week_start_id,
					sow_week_end_id: variety.sow_week_end_id,
					planting_conditions_id: variety.planting_conditions.planting_condition_id,
					soil_ph: variety.soil_ph,
					plant_depth_cm: variety.plant_depth_cm,
					plant_space_cm: variety.plant_space_cm,
					water_frequency_id: variety.water_frequency?.frequency_id,
					high_temp_water_frequency_id: variety.high_temp_water_frequency?.frequency_id,
					harvest_week_start_id: variety.harvest_week_start_id,
					harvest_week_end_id: variety.harvest_week_end_id,
					feed_frequency_id: undefined, // Not in current schema
					feed_id: undefined, // Not in current schema
			  }
			: {},
	});

	// Reset form when variety changes or modal opens/closes
	useEffect(() => {
		if (isOpen) {
			if (isEditing && variety) {
				reset({
					variety_name: variety.variety_name,
					family_id: variety.family.family_id,
					lifecycle_id: variety.lifecycle.lifecycle_id,
					sow_week_start_id: variety.sow_week_start_id,
					sow_week_end_id: variety.sow_week_end_id,
					planting_conditions_id: variety.planting_conditions.planting_condition_id,
					soil_ph: variety.soil_ph,
					plant_depth_cm: variety.plant_depth_cm,
					plant_space_cm: variety.plant_space_cm,
					water_frequency_id: variety.water_frequency?.frequency_id,
					high_temp_water_frequency_id: variety.high_temp_water_frequency?.frequency_id,
					harvest_week_start_id: variety.harvest_week_start_id,
					harvest_week_end_id: variety.harvest_week_end_id,
				});
			} else {
				reset({});
			}
		}
	}, [isOpen, isEditing, variety, reset]);

	const handleFormSubmit = (data: CreateVarietyFormData | UpdateVarietyFormData) => {
		onSubmit(data);
	};

	const handleClose = () => {
		reset();
		onClose();
	};

	if (optionsLoading) {
		return (
			<Dialog open={isOpen} onOpenChange={handleClose}>
				<DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
					<div className="flex items-center justify-center py-8">
						<Loader2 className="h-8 w-8 animate-spin" />
						<span className="ml-2">Loading form options...</span>
					</div>
				</DialogContent>
			</Dialog>
		);
	}

	return (
		<Dialog open={isOpen} onOpenChange={handleClose}>
			<DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle>
						{isEditing ? "Edit Grow Guide" : "Create New Grow Guide"}
					</DialogTitle>
					<DialogDescription>
						{isEditing
							? "Update the details for your grow guide."
							: "Add a new variety to your grow guide collection."}
					</DialogDescription>
				</DialogHeader>

				<form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
					<div className="grid gap-6">
						{/* Basic Information */}
						<div className="space-y-4">
							<h3 className="text-lg font-semibold">Basic Information</h3>
							
							<div className="grid gap-4">
								<div>
									<Label htmlFor="variety_name">Variety Name *</Label>
									<Input
										id="variety_name"
										{...register("variety_name")}
										placeholder="e.g., Cherry Tomato"
									/>
									{errors.variety_name && (
										<p className="text-sm text-destructive mt-1">
											{errors.variety_name.message}
										</p>
									)}
								</div>

								<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
									<div>
										<Label htmlFor="family_id">Plant Family *</Label>
										<Controller
											name="family_id"
											control={control}
											render={({ field }) => (
												<Select onValueChange={field.onChange} value={field.value}>
													<SelectTrigger>
														<SelectValue placeholder="Select plant family" />
													</SelectTrigger>
													<SelectContent>
														{options?.families.map((family) => (
															<SelectItem key={family.family_id} value={family.family_id}>
																{family.family_name}
															</SelectItem>
														))}
													</SelectContent>
												</Select>
											)}
										/>
										{errors.family_id && (
											<p className="text-sm text-destructive mt-1">
												{errors.family_id.message}
											</p>
										)}
									</div>

									<div>
										<Label htmlFor="lifecycle_id">Lifecycle *</Label>
										<Controller
											name="lifecycle_id"
											control={control}
											render={({ field }) => (
												<Select onValueChange={field.onChange} value={field.value}>
													<SelectTrigger>
														<SelectValue placeholder="Select lifecycle" />
													</SelectTrigger>
													<SelectContent>
														{options?.lifecycles.map((lifecycle) => (
															<SelectItem key={lifecycle.lifecycle_id} value={lifecycle.lifecycle_id}>
																{lifecycle.lifecycle_name} ({lifecycle.productivity_years} year{lifecycle.productivity_years !== 1 ? 's' : ''})
															</SelectItem>
														))}
													</SelectContent>
												</Select>
											)}
										/>
										{errors.lifecycle_id && (
											<p className="text-sm text-destructive mt-1">
												{errors.lifecycle_id.message}
											</p>
										)}
									</div>
								</div>
							</div>
						</div>

						{/* Sowing Information */}
						<div className="space-y-4">
							<h3 className="text-lg font-semibold">Sowing Schedule</h3>
							
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								<div>
									<Label htmlFor="sow_week_start_id">Sow Start Week *</Label>
									<Controller
										name="sow_week_start_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="Start week" />
												</SelectTrigger>
												<SelectContent>
													{options?.weeks.map((week) => (
														<SelectItem key={week.week_id} value={week.week_id}>
															Week {week.week_number} ({week.week_start_date} - {week.week_end_date})
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.sow_week_start_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.sow_week_start_id.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="sow_week_end_id">Sow End Week *</Label>
									<Controller
										name="sow_week_end_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="End week" />
												</SelectTrigger>
												<SelectContent>
													{options?.weeks.map((week) => (
														<SelectItem key={week.week_id} value={week.week_id}>
															Week {week.week_number} ({week.week_start_date} - {week.week_end_date})
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.sow_week_end_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.sow_week_end_id.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="planting_conditions_id">Planting Conditions *</Label>
									<Controller
										name="planting_conditions_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="Select conditions" />
												</SelectTrigger>
												<SelectContent>
													{options?.planting_conditions.map((condition) => (
														<SelectItem key={condition.planting_condition_id} value={condition.planting_condition_id}>
															{condition.planting_condition}
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.planting_conditions_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.planting_conditions_id.message}
										</p>
									)}
								</div>
							</div>
						</div>

						{/* Growing Details */}
						<div className="space-y-4">
							<h3 className="text-lg font-semibold">Growing Details</h3>
							
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								<div>
									<Label htmlFor="soil_ph">Soil pH</Label>
									<Input
										id="soil_ph"
										type="number"
										step="0.1"
										min="0"
										max="14"
										{...register("soil_ph", { valueAsNumber: true })}
										placeholder="6.5"
									/>
									{errors.soil_ph && (
										<p className="text-sm text-destructive mt-1">
											{errors.soil_ph.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="plant_depth_cm">Planting Depth (cm)</Label>
									<Input
										id="plant_depth_cm"
										type="number"
										step="0.1"
										min="0.1"
										{...register("plant_depth_cm", { valueAsNumber: true })}
										placeholder="2.0"
									/>
									{errors.plant_depth_cm && (
										<p className="text-sm text-destructive mt-1">
											{errors.plant_depth_cm.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="plant_space_cm">Plant Spacing (cm)</Label>
									<Input
										id="plant_space_cm"
										type="number"
										min="1"
										{...register("plant_space_cm", { valueAsNumber: true })}
										placeholder="30"
									/>
									{errors.plant_space_cm && (
										<p className="text-sm text-destructive mt-1">
											{errors.plant_space_cm.message}
										</p>
									)}
								</div>
							</div>
						</div>

						{/* Watering */}
						<div className="space-y-4">
							<h3 className="text-lg font-semibold">Watering Schedule</h3>
							
							<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div>
									<Label htmlFor="water_frequency_id">Water Frequency</Label>
									<Controller
										name="water_frequency_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="Select frequency" />
												</SelectTrigger>
												<SelectContent>
													{options?.frequencies.map((frequency) => (
														<SelectItem key={frequency.frequency_id} value={frequency.frequency_id}>
															{frequency.frequency_name} ({frequency.frequency_days_per_year} days/year)
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.water_frequency_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.water_frequency_id.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="high_temp_water_frequency_id">High Temperature Frequency</Label>
									<Controller
										name="high_temp_water_frequency_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="Select frequency" />
												</SelectTrigger>
												<SelectContent>
													{options?.frequencies.map((frequency) => (
														<SelectItem key={frequency.frequency_id} value={frequency.frequency_id}>
															{frequency.frequency_name} ({frequency.frequency_days_per_year} days/year)
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.high_temp_water_frequency_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.high_temp_water_frequency_id.message}
										</p>
									)}
								</div>
							</div>
						</div>

						{/* Harvest Information */}
						<div className="space-y-4">
							<h3 className="text-lg font-semibold">Harvest Schedule</h3>
							
							<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div>
									<Label htmlFor="harvest_week_start_id">Harvest Start Week</Label>
									<Controller
										name="harvest_week_start_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="Start week" />
												</SelectTrigger>
												<SelectContent>
													{options?.weeks.map((week) => (
														<SelectItem key={week.week_id} value={week.week_id}>
															Week {week.week_number} ({week.week_start_date} - {week.week_end_date})
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.harvest_week_start_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.harvest_week_start_id.message}
										</p>
									)}
								</div>

								<div>
									<Label htmlFor="harvest_week_end_id">Harvest End Week</Label>
									<Controller
										name="harvest_week_end_id"
										control={control}
										render={({ field }) => (
											<Select onValueChange={field.onChange} value={field.value}>
												<SelectTrigger>
													<SelectValue placeholder="End week" />
												</SelectTrigger>
												<SelectContent>
													{options?.weeks.map((week) => (
														<SelectItem key={week.week_id} value={week.week_id}>
															Week {week.week_number} ({week.week_start_date} - {week.week_end_date})
														</SelectItem>
													))}
												</SelectContent>
											</Select>
										)}
									/>
									{errors.harvest_week_end_id && (
										<p className="text-sm text-destructive mt-1">
											{errors.harvest_week_end_id.message}
										</p>
									)}
								</div>
							</div>
						</div>
					</div>

					{error && <FormError message={error} />}

					<DialogFooter>
						<Button
							type="button"
							variant="outline"
							onClick={handleClose}
							disabled={isLoading}
						>
							<X className="h-4 w-4 mr-1" />
							Cancel
						</Button>
						<Button type="submit" disabled={isLoading}>
							{isLoading ? (
								<>
									<Loader2 className="h-4 w-4 animate-spin mr-1" />
									{isEditing ? "Updating..." : "Creating..."}
								</>
							) : (
								<>
									<Save className="h-4 w-4 mr-1" />
									{isEditing ? "Update Guide" : "Create Guide"}
								</>
							)}
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
}
