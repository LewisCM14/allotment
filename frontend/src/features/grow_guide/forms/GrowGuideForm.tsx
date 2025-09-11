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

// Centralised field metadata to control labels & required marker
const FIELD_META: Record<string, { label: string; required?: boolean }> = {
	variety_name: { label: "Variety Name", required: true },
	family_id: { label: "Plant Family", required: true },
	lifecycle_id: { label: "Lifecycle", required: true },
	sow_week_start_id: { label: "Sowing Start Week", required: true },
	sow_week_end_id: { label: "Sowing End Week", required: true },
	transplant_week_start_id: { label: "Transplant Start Week" },
	transplant_week_end_id: { label: "Transplant End Week" },
	planting_conditions_id: { label: "Planting Conditions", required: true },
	soil_ph: { label: "Soil pH", required: true },
	plant_depth_cm: { label: "Plant Depth (cm)", required: true },
	plant_space_cm: { label: "Plant Spacing (cm)", required: true },
	row_width_cm: { label: "Row Width (cm)" },
	feed_id: { label: "Feed Type" },
	feed_week_start_id: { label: "Feed Start Week" },
	feed_frequency_id: { label: "Feed Frequency" },
	water_frequency_id: { label: "Water Frequency", required: true },
	high_temp_degrees: { label: "High Temperature Threshold" },
	high_temp_water_frequency_id: { label: "High Temp Water Frequency" },
	harvest_week_start_id: { label: "Harvest Start Week", required: true },
	harvest_week_end_id: { label: "Harvest End Week", required: true },
	prune_week_start_id: { label: "Prune Start Week" },
	prune_week_end_id: { label: "Prune End Week" },
	notes: { label: "Notes" },
	is_public: { label: "Make this grow guide public" },
};

const labelFor = (name: keyof typeof FIELD_META) => {
	const meta = FIELD_META[name];
	return meta.required ? `${meta.label}*` : meta.label;
};

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
	const {
		data: options,
		isLoading: isLoadingOptions,
		isError: isOptionsError,
	} = useGrowGuideOptions();

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

	// Option data (no hardcoded fallbacks; rely entirely on API)
	const families: Option[] = (options?.families ?? []).map((f) => ({
		value: f.family_id,
		label: f.family_name,
	}));

	const lifecycles: Option[] = (options?.lifecycles ?? []).map((l) => ({
		value: l.lifecycle_id,
		label: l.lifecycle_name,
	}));

	const feedTypes: Option[] = (options?.feeds ?? []).map((f) => ({
		value: f.feed_id,
		label: f.feed_name,
	}));

	const frequencies: Option[] = (options?.frequencies ?? []).map((f) => ({
		value: f.frequency_id,
		label: f.frequency_name,
	}));

	const weeks: Option[] = (options?.weeks ?? []).map((w) => {
		const num = w.week_number?.toString().padStart(2, "0");
		const start = w.week_start_date || ""; // expected format MM/DD
		return {
			value: w.week_id,
			label: `${start} - Week ${num}`.trim(),
		};
	});

	const plantingConditions: Option[] = (options?.planting_conditions ?? []).map(
		(p) => ({
			value: p.planting_condition_id,
			label: p.planting_condition,
		}),
	);

	const days: Option[] = (options?.days ?? []).map((d) => ({
		value: d.day_id,
		label: d.day_name,
	}));

	// Detect missing critical option sets after load
	const coreSetsMissing =
		families.length === 0 ||
		lifecycles.length === 0 ||
		plantingConditions.length === 0 ||
		weeks.length === 0 ||
		frequencies.length === 0;

	// Only flag missing after load completes (no spinner) and no transport error
	const missingCoreOptions =
		!isLoadingOptions && !isOptionsError && coreSetsMissing;

	return (
		<Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
			<DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="text-2xl font-bold">
						Add New Grow Guide
					</DialogTitle>
				</DialogHeader>

				{isLoadingOptions ? (
					<div className="py-6 text-sm text-muted-foreground">
						Loading options...
					</div>
				) : isOptionsError ? (
					<div className="py-6 space-y-4">
						<p className="text-sm text-destructive">
							Failed to load grow guide options. Please try again later.
						</p>
						<DialogFooter className="pt-2">
							<Button type="button" variant="outline" onClick={onClose}>
								Close
							</Button>
						</DialogFooter>
					</div>
				) : missingCoreOptions ? (
					<div className="py-6 space-y-4">
						<p className="text-sm text-muted-foreground">
							Required option data couldn't be loaded. Please close and reopen
							the form or try again later.
						</p>
						<ul className="text-xs list-disc pl-5 space-y-1 text-muted-foreground">
							{families.length === 0 && <li>Plant families unavailable</li>}
							{lifecycles.length === 0 && <li>Lifecycles unavailable</li>}
							{plantingConditions.length === 0 && (
								<li>Planting conditions unavailable</li>
							)}
							{weeks.length === 0 && <li>Weeks unavailable</li>}
							{frequencies.length === 0 && <li>Frequencies unavailable</li>}
						</ul>
						<DialogFooter className="pt-2">
							<Button type="button" variant="outline" onClick={onClose}>
								Close
							</Button>
						</DialogFooter>
					</div>
				) : (
					<form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
						<div className="space-y-2">
							<Label htmlFor="variety_name">{labelFor("variety_name")}</Label>
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
								<Label htmlFor="family_id">{labelFor("family_id")}</Label>
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
								<Label htmlFor="lifecycle_id">{labelFor("lifecycle_id")}</Label>
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
								<Label htmlFor="sow_week_start_id">{labelFor("sow_week_start_id")}</Label>
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
								<Label htmlFor="sow_week_end_id">{labelFor("sow_week_end_id")}</Label>
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
								<Label htmlFor="transplant_week_start_id">{labelFor("transplant_week_start_id")}</Label>
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
									<FormError
										message={errors.transplant_week_start_id.message}
									/>
								)}
							</div>

							<div className="space-y-2">
								<Label htmlFor="transplant_week_end_id">{labelFor("transplant_week_end_id")}</Label>
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
							<Label htmlFor="planting_conditions_id">{labelFor("planting_conditions_id")}</Label>
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
								<Label htmlFor="soil_ph">{labelFor("soil_ph")}</Label>
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
								{errors.soil_ph && (
									<FormError message={errors.soil_ph.message} />
								)}
							</div>

							<div className="space-y-2">
								<Label htmlFor="plant_depth_cm">{labelFor("plant_depth_cm")}</Label>
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
								<Label htmlFor="plant_space_cm">{labelFor("plant_space_cm")}</Label>
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
							<Label htmlFor="row_width_cm">{labelFor("row_width_cm")}</Label>
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
								<Label htmlFor="feed_id">{labelFor("feed_id")}</Label>
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
								{errors.feed_id && (
									<FormError message={errors.feed_id.message} />
								)}
							</div>

							<div className="space-y-2">
								<Label htmlFor="feed_week_start_id">{labelFor("feed_week_start_id")}</Label>
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
								<Label htmlFor="feed_frequency_id">{labelFor("feed_frequency_id")}</Label>
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
								<Label htmlFor="water_frequency_id">{labelFor("water_frequency_id")}</Label>
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
								<Label htmlFor="high_temp_degrees">{labelFor("high_temp_degrees")}</Label>
								<Input
									id="high_temp_degrees"
									type="number"
									{...register("high_temp_degrees", { valueAsNumber: true })}
									placeholder="e.g. 30"
									className={
										errors.high_temp_degrees ? "border-destructive" : ""
									}
								/>
								{errors.high_temp_degrees && (
									<FormError message={errors.high_temp_degrees.message} />
								)}
							</div>

							<div className="space-y-2">
								<Label htmlFor="high_temp_water_frequency_id">{labelFor("high_temp_water_frequency_id")}</Label>
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
								<Label htmlFor="harvest_week_start_id">{labelFor("harvest_week_start_id")}</Label>
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
								<Label htmlFor="harvest_week_end_id">{labelFor("harvest_week_end_id")}</Label>
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
								<Label htmlFor="prune_week_start_id">{labelFor("prune_week_start_id")}</Label>
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
								<Label htmlFor="prune_week_end_id">{labelFor("prune_week_end_id")}</Label>
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
							<Label htmlFor="notes">{labelFor("notes")}</Label>
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
							<Label htmlFor="is_public">{labelFor("is_public")}</Label>
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
				)}
			</DialogContent>
		</Dialog>
	);
};
