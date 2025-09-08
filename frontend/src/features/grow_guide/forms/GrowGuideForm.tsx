import { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { FormError } from "../../../components/FormError";
import { Switch } from "../../../components/ui/Switch";
import { Checkbox } from "../../../components/ui/Checkbox";
import { Textarea } from "../../../components/ui/Textarea";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogFooter,
} from "../../../components/ui/Dialog";
import { FormSelect } from "../components/FormSelect";
import {
	growGuideFormSchema,
	type GrowGuideFormData,
} from "./GrowGuideFormSchema";
import { useCreateGrowGuide } from "../hooks/useCreateGrowGuide";
import { useGrowGuideOptions } from "../hooks/useGrowGuideOptions";
import { toast } from "sonner";

// Define interface for option objects
interface Option {
	value: string;
	label: string;
}

interface GrowGuideFormProps {
	isOpen: boolean;
	onClose: () => void;
	onSuccess?: () => void;
}

/**
 * Form component for creating a new grow guide
 */
export const GrowGuideForm = ({
	isOpen,
	onClose,
	onSuccess,
}: GrowGuideFormProps) => {
	const [isSubmitting, setIsSubmitting] = useState(false);

	// Get options from API
	const { data: options, isLoading: isLoadingOptions } = useGrowGuideOptions();

	const {
		register,
		handleSubmit,
		formState: { errors },
		control,
		reset,
		setValue,
	} = useForm<GrowGuideFormData>({
		resolver: zodResolver(growGuideFormSchema),
		defaultValues: {
			variety_name: "",
			family_id: "",
			lifecycle_id: "",
			sow_week_start_id: "",
			sow_week_end_id: "",
			planting_conditions_id: "",
			soil_ph: 7.0,
			plant_depth_cm: 5,
			plant_space_cm: 30,
			water_frequency_id: "",
			harvest_week_start_id: "",
			harvest_week_end_id: "",
			feed_id: "",
			feed_frequency_id: "",
			feed_week_start_id: "",
			high_temp_degrees: undefined,
			high_temp_water_frequency_id: "",
			prune_week_start_id: "",
			prune_week_end_id: "",
			notes: "",
			is_public: false,
			water_days: [],
		},
	});

	const createGrowGuideMutation = useCreateGrowGuide();

	const onSubmit = async (data: GrowGuideFormData) => {
		setIsSubmitting(true);
		try {
			// Convert numeric string fields to numbers
			const formData = {
				...data,
				soil_ph: Number(data.soil_ph),
				plant_depth_cm: Number(data.plant_depth_cm),
				plant_space_cm: Number(data.plant_space_cm),
				row_width_cm: data.row_width_cm ? Number(data.row_width_cm) : undefined,
				high_temp_degrees: data.high_temp_degrees
					? Number(data.high_temp_degrees)
					: undefined,
			};

			await createGrowGuideMutation.mutateAsync(formData);
			toast.success("Grow guide created successfully");
			reset();
			onSuccess?.();
			onClose();
		} catch (error) {
			const message =
				error instanceof Error ? error.message : "Failed to create grow guide";
			toast.error(message);
		} finally {
			setIsSubmitting(false);
		}
	};

	// Default mocked options in case API is not ready
	const families = options?.families?.map((f) => ({
		value: f.family_id,
		label: f.family_name,
	})) || [
		{ value: "1", label: "Solanaceae (Nightshade)" },
		{ value: "2", label: "Brassicaceae (Cabbage)" },
		{ value: "3", label: "Fabaceae (Legume)" },
	];

	const lifecycles = options?.lifecycles?.map((l) => ({
		value: l.lifecycle_id,
		label: l.lifecycle_name,
	})) || [
		{ value: "1", label: "Annual" },
		{ value: "2", label: "Biennial" },
		{ value: "3", label: "Perennial" },
	];

	const feedTypes = options?.feeds?.map((f) => ({
		value: f.feed_id,
		label: f.feed_name,
	})) || [
		{ value: "1", label: "Nitrogen-Rich" },
		{ value: "2", label: "Phosphorus-Rich" },
		{ value: "3", label: "Potassium-Rich" },
		{ value: "4", label: "Balanced" },
	];

	const frequencies = options?.frequencies?.map((f) => ({
		value: f.frequency_id,
		label: f.frequency_name,
	})) || [
		{ value: "1", label: "Daily" },
		{ value: "2", label: "Weekly" },
		{ value: "3", label: "Bi-Weekly" },
		{ value: "4", label: "Monthly" },
	];

	const weeks =
		options?.weeks?.map((w) => ({
			value: w.week_id,
			label: `Week ${w.week_number}`,
		})) ||
		Array.from({ length: 52 }, (_, i) => ({
			value: (i + 1).toString(),
			label: `Week ${i + 1}`,
		}));

	const plantingConditions = options?.planting_conditions?.map((p) => ({
		value: p.planting_condition_id,
		label: p.planting_condition,
	})) || [
		{ value: "1", label: "Full Sun" },
		{ value: "2", label: "Partial Shade" },
		{ value: "3", label: "Full Shade" },
	];

	const days = options?.days?.map((d) => ({
		value: d.day_id,
		label: d.day_name,
	})) || [
		{ value: "1", label: "Monday" },
		{ value: "2", label: "Tuesday" },
		{ value: "3", label: "Wednesday" },
		{ value: "4", label: "Thursday" },
		{ value: "5", label: "Friday" },
		{ value: "6", label: "Saturday" },
		{ value: "7", label: "Sunday" },
	];

	return (
		<Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
			<DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="text-2xl font-bold">
						Add New Grow Guide
					</DialogTitle>
				</DialogHeader>
				<form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
					<div className="space-y-2">
						<Label htmlFor="variety_name">Variety Name</Label>
						<Input
							id="variety_name"
							{...register("variety_name")}
							placeholder="e.g. Roma Tomato"
							className={errors.variety_name ? "border-destructive" : ""}
						/>
						{errors.variety_name && (
							<FormError message={errors.variety_name.message} />
						)}
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="family_id">Plant Family</Label>
							<Controller
								name="family_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="family_id"
										placeholder="Select plant family"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={families}
										error={!!errors.family_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.family_id && (
								<FormError message={errors.family_id.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="lifecycle_id">Lifecycle</Label>
							<Controller
								name="lifecycle_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="lifecycle_id"
										placeholder="Select lifecycle"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={lifecycles}
										error={!!errors.lifecycle_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.lifecycle_id && (
								<FormError message={errors.lifecycle_id.message} />
							)}
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="sow_week_start_id">Sowing Start Week</Label>
							<Controller
								name="sow_week_start_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="sow_week_start_id"
										placeholder="Select start week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.sow_week_start_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.sow_week_start_id && (
								<FormError message={errors.sow_week_start_id.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="sow_week_end_id">Sowing End Week</Label>
							<Controller
								name="sow_week_end_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="sow_week_end_id"
										placeholder="Select end week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.sow_week_end_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.sow_week_end_id && (
								<FormError message={errors.sow_week_end_id.message} />
							)}
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="transplant_week_start_id">
								Transplant Start Week (optional)
							</Label>
							<Controller
								name="transplant_week_start_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="transplant_week_start_id"
										placeholder="Select start week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.transplant_week_start_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.transplant_week_start_id && (
								<FormError message={errors.transplant_week_start_id.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="transplant_week_end_id">
								Transplant End Week (optional)
							</Label>
							<Controller
								name="transplant_week_end_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="transplant_week_end_id"
										placeholder="Select end week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.transplant_week_end_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.transplant_week_end_id && (
								<FormError message={errors.transplant_week_end_id.message} />
							)}
						</div>
					</div>

					<div className="space-y-2">
						<Label htmlFor="planting_conditions_id">Planting Conditions</Label>
						<Controller
							name="planting_conditions_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="planting_conditions_id"
									placeholder="Select planting conditions"
									value={field.value || ""}
									onValueChange={field.onChange}
									options={plantingConditions}
									error={!!errors.planting_conditions_id}
									disabled={isLoadingOptions}
								/>
							)}
						/>
						{errors.planting_conditions_id && (
							<FormError message={errors.planting_conditions_id.message} />
						)}
					</div>

					<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div className="space-y-2">
							<Label htmlFor="soil_ph">Soil pH</Label>
							<Input
								id="soil_ph"
								type="number"
								step="0.1"
								min="0"
								max="14"
								{...register("soil_ph", { valueAsNumber: true })}
								placeholder="e.g. 7.0"
								className={errors.soil_ph ? "border-destructive" : ""}
							/>
							{errors.soil_ph && <FormError message={errors.soil_ph.message} />}
						</div>

						<div className="space-y-2">
							<Label htmlFor="plant_depth_cm">Plant Depth (cm)</Label>
							<Input
								id="plant_depth_cm"
								type="number"
								min="1"
								max="100"
								{...register("plant_depth_cm", { valueAsNumber: true })}
								placeholder="e.g. 5"
								className={errors.plant_depth_cm ? "border-destructive" : ""}
							/>
							{errors.plant_depth_cm && (
								<FormError message={errors.plant_depth_cm.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="plant_space_cm">Plant Spacing (cm)</Label>
							<Input
								id="plant_space_cm"
								type="number"
								min="1"
								max="1000"
								{...register("plant_space_cm", { valueAsNumber: true })}
								placeholder="e.g. 30"
								className={errors.plant_space_cm ? "border-destructive" : ""}
							/>
							{errors.plant_space_cm && (
								<FormError message={errors.plant_space_cm.message} />
							)}
						</div>
					</div>

					<div className="space-y-2">
						<Label htmlFor="row_width_cm">Row Width (cm) (optional)</Label>
						<Input
							id="row_width_cm"
							type="number"
							min="1"
							max="1000"
							{...register("row_width_cm", { valueAsNumber: true })}
							placeholder="e.g. 60"
							className={errors.row_width_cm ? "border-destructive" : ""}
						/>
						{errors.row_width_cm && (
							<FormError message={errors.row_width_cm.message} />
						)}
					</div>

					<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div className="space-y-2">
							<Label htmlFor="feed_id">Feed Type (optional)</Label>
							<Controller
								name="feed_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="feed_id"
										placeholder="Select feed type"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={feedTypes}
										error={!!errors.feed_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.feed_id && <FormError message={errors.feed_id.message} />}
						</div>

						<div className="space-y-2">
							<Label htmlFor="feed_week_start_id">
								Feed Start Week (optional)
							</Label>
							<Controller
								name="feed_week_start_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="feed_week_start_id"
										placeholder="Select feed start week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.feed_week_start_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.feed_week_start_id && (
								<FormError message={errors.feed_week_start_id.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="feed_frequency_id">
								Feed Frequency (optional)
							</Label>
							<Controller
								name="feed_frequency_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="feed_frequency_id"
										placeholder="Select feed frequency"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={frequencies}
										error={!!errors.feed_frequency_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.feed_frequency_id && (
								<FormError message={errors.feed_frequency_id.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="water_frequency_id">Water Frequency</Label>
							<Controller
								name="water_frequency_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="water_frequency_id"
										placeholder="Select water frequency"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={frequencies}
										error={!!errors.water_frequency_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.water_frequency_id && (
								<FormError message={errors.water_frequency_id.message} />
							)}
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="high_temp_degrees">
								High Temperature Threshold (optional)
							</Label>
							<Input
								id="high_temp_degrees"
								type="number"
								{...register("high_temp_degrees", { valueAsNumber: true })}
								placeholder="e.g. 30"
								className={errors.high_temp_degrees ? "border-destructive" : ""}
							/>
							{errors.high_temp_degrees && (
								<FormError message={errors.high_temp_degrees.message} />
							)}
						</div>

						<div className="space-y-2">
							<Label htmlFor="high_temp_water_frequency_id">
								High Temp Water Frequency
							</Label>
							<Controller
								name="high_temp_water_frequency_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="high_temp_water_frequency_id"
										placeholder="Select high temp water frequency"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={frequencies}
										error={!!errors.high_temp_water_frequency_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.high_temp_water_frequency_id && (
								<FormError
									message={errors.high_temp_water_frequency_id.message}
								/>
							)}
						</div>
					</div>

					<div className="space-y-2">
						<Label>Watering Days</Label>
						<div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
							{days.map((day) => (
								<div key={day.value} className="flex items-center space-x-2">
									<Controller
										name="water_days"
										control={control}
										render={({ field }) => {
											const isSelected = field.value.some(
												(d: { day_id: string }) => d.day_id === day.value,
											);
											return (
												<Checkbox
													id={`day-${day.value}`}
													checked={isSelected}
													onCheckedChange={(checked: boolean) => {
														if (checked) {
															field.onChange([
																...field.value,
																{ day_id: day.value },
															]);
														} else {
															field.onChange(
																field.value.filter(
																	(d: { day_id: string }) =>
																		d.day_id !== day.value,
																),
															);
														}
													}}
												/>
											);
										}}
									/>
									<Label
										htmlFor={`day-${day.value}`}
										className="cursor-pointer"
									>
										{day.label}
									</Label>
								</div>
							))}
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="harvest_week_start_id">Harvest Start Week</Label>
							<Controller
								name="harvest_week_start_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="harvest_week_start_id"
										placeholder="Select harvest start week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.harvest_week_start_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.harvest_week_start_id && (
								<FormError message={errors.harvest_week_start_id.message} />
							)}
						</div>
						<div className="space-y-2">
							<Label htmlFor="harvest_week_end_id">Harvest End Week</Label>
							<Controller
								name="harvest_week_end_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="harvest_week_end_id"
										placeholder="Select harvest end week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.harvest_week_end_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.harvest_week_end_id && (
								<FormError message={errors.harvest_week_end_id.message} />
							)}
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label htmlFor="prune_week_start_id">
								Prune Start Week (optional)
							</Label>
							<Controller
								name="prune_week_start_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="prune_week_start_id"
										placeholder="Select prune start week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.prune_week_start_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.prune_week_start_id && (
								<FormError message={errors.prune_week_start_id.message} />
							)}
						</div>
						<div className="space-y-2">
							<Label htmlFor="prune_week_end_id">
								Prune End Week (optional)
							</Label>
							<Controller
								name="prune_week_end_id"
								control={control}
								render={({ field }) => (
									<FormSelect
										id="prune_week_end_id"
										placeholder="Select prune end week"
										value={field.value || ""}
										onValueChange={field.onChange}
										options={weeks}
										error={!!errors.prune_week_end_id}
										disabled={isLoadingOptions}
									/>
								)}
							/>
							{errors.prune_week_end_id && (
								<FormError message={errors.prune_week_end_id.message} />
							)}
						</div>
					</div>

					<div className="space-y-2">
						<Label htmlFor="notes">Notes</Label>
						<Textarea
							id="notes"
							{...register("notes")}
							placeholder="Optional notes about this grow guide (minimum 5 characters)"
							className={errors.notes ? "border-destructive" : ""}
						/>
						{errors.notes && <FormError message={errors.notes.message} />}
					</div>

					<div className="flex items-center space-x-2">
						<Controller
							name="is_public"
							control={control}
							render={({ field }) => (
								<Switch
									id="is_public"
									checked={field.value}
									onCheckedChange={field.onChange}
								/>
							)}
						/>
						<Label htmlFor="is_public">Make this grow guide public</Label>
					</div>

					<DialogFooter className="pt-4">
						<Button
							type="button"
							variant="outline"
							onClick={onClose}
							disabled={isSubmitting}
						>
							Cancel
						</Button>
						<Button type="submit" disabled={isSubmitting}>
							{isSubmitting ? "Creating..." : "Create Guide"}
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
};
