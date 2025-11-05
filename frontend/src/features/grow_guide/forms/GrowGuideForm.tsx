import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { FormError } from "../../../components/FormError";
import { Button } from "../../../components/ui/Button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "../../../components/ui/Dialog";
import { FormSelect } from "../../../components/ui/FormSelect";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Switch } from "../../../components/ui/Switch";
import { Textarea } from "../../../components/ui/Textarea";
import { useCreateGrowGuide } from "../hooks/useCreateGrowGuide";
import { useGrowGuide } from "../hooks/useGrowGuide";
import { useGrowGuideOptions } from "../hooks/useGrowGuideOptions";
import { growGuideService } from "../services/growGuideService";
import {
	type GrowGuideFormData,
	growGuideFormSchema,
} from "./GrowGuideFormSchema";

// Centralized field metadata to control labels & required marker
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
	high_temp_degrees: { label: "High Temperature Threshold", required: true },
	high_temp_water_frequency_id: {
		label: "High Temp Water Frequency",
		required: true,
	},
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

const formatWeekStart = (raw?: string | null): string | undefined => {
	if (!raw) return undefined;
	const trimmed = raw.trim();
	if (trimmed === "") return undefined;
	// Accept ISO (YYYY-MM-DD) or already formatted MM/DD strings.
	if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
		const [, month, day] = trimmed.split("-");
		return `${month}/${day}`;
	}
	if (/^\d{2}\/\d{2}$/.test(trimmed)) {
		return trimmed;
	}
	return trimmed;
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
	varietyId?: string | null; // when provided, enables edit/view mode
	mode?: "create" | "edit" | "view"; // add view-only mode
}

/**
 * Form component for creating a new grow guide
 */
export const GrowGuideForm = ({
	isOpen,
	onClose,
	onSuccess,
	varietyId,
	mode = "create",
}: GrowGuideFormProps) => {
	const [isSubmitting, setIsSubmitting] = useState(false);
	// Incremented after we programmatically populate the form to force Radix Selects to re-evaluate their item list
	const [populateTick, setPopulateTick] = useState(0);
	const queryClient = useQueryClient();

	// Load existing guide when editing
	const {
		data: existingGuide,
		isLoading: isLoadingGuide,
		isError: isGuideError,
	} = useGrowGuide(varietyId && mode !== "create" ? varietyId : undefined);

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
		defaultValues: (() => {
			const initialDefaults: GrowGuideFormData = {
				variety_name: "",
				family_id: "",
				lifecycle_id: "",
				sow_week_start_id: "",
				sow_week_end_id: "",
				transplant_week_start_id: "",
				transplant_week_end_id: "",
				planting_conditions_id: "",
				soil_ph: undefined as unknown as number,
				plant_depth_cm: undefined as unknown as number,
				plant_space_cm: undefined as unknown as number,
				row_width_cm: undefined,
				water_frequency_id: "",
				harvest_week_start_id: "",
				harvest_week_end_id: "",
				feed_id: "",
				feed_frequency_id: "",
				feed_week_start_id: "",
				high_temp_degrees: undefined as unknown as number,
				high_temp_water_frequency_id: "",
				prune_week_start_id: "",
				prune_week_end_id: "",
				notes: undefined,
				is_public: false,
			};
			return initialDefaults;
		})(),
	});

	const createGrowGuideMutation = useCreateGrowGuide();

	const resetToBlank = useCallback(() => {
		reset({
			variety_name: "",
			family_id: "",
			lifecycle_id: "",
			sow_week_start_id: "",
			sow_week_end_id: "",
			transplant_week_start_id: "",
			transplant_week_end_id: "",
			planting_conditions_id: "",
			soil_ph: undefined as unknown as number,
			plant_depth_cm: undefined as unknown as number,
			plant_space_cm: undefined as unknown as number,
			row_width_cm: undefined,
			water_frequency_id: "",
			harvest_week_start_id: "",
			harvest_week_end_id: "",
			feed_id: "",
			feed_frequency_id: "",
			feed_week_start_id: "",
			high_temp_degrees: undefined as unknown as number,
			high_temp_water_frequency_id: "",
			prune_week_start_id: "",
			prune_week_end_id: "",
			notes: undefined,
			is_public: false,
		});
		setTimeout(() => {
			setValue("soil_ph", undefined as unknown as number);
			setValue("plant_depth_cm", undefined as unknown as number);
			setValue("plant_space_cm", undefined as unknown as number);
			setValue("row_width_cm", undefined);
			setValue("high_temp_degrees", undefined as unknown as number);
		}, 0);
	}, [reset, setValue]);

	const onSubmit = useCallback(
		async (data: GrowGuideFormData) => {
			setIsSubmitting(true);
			try {
				const formData = {
					...data,
				};

				if (mode === "create") {
					await createGrowGuideMutation.mutateAsync(formData);
					toast.success("Grow guide created successfully");
					resetToBlank();
				} else if (mode === "edit" && varietyId) {
					await growGuideService.updateVariety(varietyId, formData);
					// Invalidate list + individual detail cache
					queryClient.invalidateQueries({ queryKey: ["userGrowGuides"] });
					queryClient.invalidateQueries({ queryKey: ["growGuide", varietyId] });
					toast.success("Grow guide updated");
				}

				onSuccess?.();
				onClose();
			} catch (error) {
				const defaultMessage =
					mode === "create"
						? "Failed to create grow guide"
						: "Failed to update grow guide";
				const message = error instanceof Error ? error.message : defaultMessage;
				toast.error(message);
			} finally {
				setIsSubmitting(false);
			}
		},
		[
			mode,
			varietyId,
			createGrowGuideMutation,
			queryClient,
			onSuccess,
			onClose,
			resetToBlank,
		],
	);

	// Populate form when viewing or editing. Relaxed gating so tests with mock IDs that don't match option IDs still populate base fields.
	useEffect(() => {
		if (
			mode === "create" ||
			!varietyId ||
			!existingGuide ||
			isLoadingGuide ||
			isLoadingOptions
		) {
			return;
		}
		// Basic guard to ensure we are still on same variety
		if (existingGuide.variety_id !== varietyId) return;
		reset({
			variety_name: existingGuide.variety_name,
			family_id: existingGuide.family.family_id,
			lifecycle_id: existingGuide.lifecycle.lifecycle_id,
			sow_week_start_id: existingGuide.sow_week_start_id,
			sow_week_end_id: existingGuide.sow_week_end_id,
			transplant_week_start_id: existingGuide.transplant_week_start_id ?? "",
			transplant_week_end_id: existingGuide.transplant_week_end_id ?? "",
			planting_conditions_id:
				existingGuide.planting_conditions.planting_condition_id,
			soil_ph: existingGuide.soil_ph as unknown as number,
			plant_depth_cm: existingGuide.plant_depth_cm as unknown as number,
			plant_space_cm: existingGuide.plant_space_cm as unknown as number,
			row_width_cm: existingGuide.row_width_cm,
			water_frequency_id: existingGuide.water_frequency.frequency_id,
			harvest_week_start_id: existingGuide.harvest_week_start_id,
			harvest_week_end_id: existingGuide.harvest_week_end_id,
			feed_id: existingGuide.feed?.feed_id ?? "",
			feed_frequency_id: existingGuide.feed_frequency?.frequency_id ?? "",
			feed_week_start_id: existingGuide.feed_week_start_id ?? "",
			high_temp_degrees: existingGuide.high_temp_degrees as unknown as number,
			high_temp_water_frequency_id:
				existingGuide.high_temp_water_frequency?.frequency_id ?? "",
			prune_week_start_id: existingGuide.prune_week_start_id ?? "",
			prune_week_end_id: existingGuide.prune_week_end_id ?? "",
			notes: existingGuide.notes ?? "",
			is_public: existingGuide.is_public,
		});
		setPopulateTick((t) => t + 1);
	}, [mode, varietyId, existingGuide, isLoadingGuide, isLoadingOptions, reset]);

	// In create mode, if the supplied varietyId prop changes (even though it's not used for edit), reset the form to blank.
	useEffect(() => {
		if (mode === "create" && varietyId) {
			resetToBlank();
		}
	}, [mode, varietyId, resetToBlank]);

	// Reset form when dialog opens in create mode
	useEffect(() => {
		if (isOpen && mode === "create") {
			resetToBlank();
		}
	}, [isOpen, mode, resetToBlank]);

	// Key used to force full form subtree re-render after programmatic population
	const formKey = useMemo(
		() =>
			mode !== "create" ? `detail-${varietyId}-${populateTick}` : "create",
		[mode, varietyId, populateTick],
	);

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

	// Feed frequencies restricted subset from backend if provided
	const feedFrequencies: Option[] = (options?.feed_frequencies ?? []).map(
		(f) => ({
			value: f.frequency_id,
			label: f.frequency_name,
		}),
	);

	const weeks: Option[] = (options?.weeks ?? []).map((w) => {
		const num =
			typeof w.week_number === "number"
				? w.week_number.toString().padStart(2, "0")
				: undefined;
		const baseLabel = num ? `Week ${num}` : "Week";
		const start = formatWeekStart(w.week_start_date);
		const parts = [] as string[];
		if (start) parts.push(start);
		parts.push(baseLabel);
		const label = parts.join(" ").trim();
		return {
			value: w.week_id,
			label,
		};
	});

	const plantingConditions: Option[] = (options?.planting_conditions ?? []).map(
		(p) => ({
			value: p.planting_condition_id,
			label: p.planting_condition,
		}),
	);

	// Helper: clear all feed-related fields together to avoid partial trio state
	const clearFeedFields = useCallback(() => {
		setValue("feed_id", "");
		setValue("feed_week_start_id", "");
		setValue("feed_frequency_id", "");
	}, [setValue]);

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

	const submittingText = mode === "create" ? "Creating..." : "Saving...";
	const idleText = mode === "create" ? "Create Guide" : "Save Changes";
	const submitButtonText = isSubmitting ? submittingText : idleText;

	const title = useMemo(() => {
		if (mode === "create") return "Add New Grow Guide";
		if (mode === "view")
			return existingGuide?.variety_name
				? `View ${existingGuide.variety_name}`
				: "View Grow Guide";
		const editTitle = existingGuide?.variety_name
			? `Edit ${existingGuide.variety_name}`
			: "Edit Grow Guide";
		return editTitle;
	}, [mode, existingGuide]);

	const dialogContent = useMemo(() => {
		if (isLoadingOptions || (isLoadingGuide && mode !== "create")) {
			return (
				<div className="py-6 text-sm text-muted-foreground">
					Loading options...
				</div>
			);
		}

		if (isOptionsError) {
			return (
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
			);
		}

		if (isGuideError) {
			return (
				<div className="py-6 space-y-4">
					<p className="text-sm text-destructive">
						Failed to load the requested grow guide. It may have been deleted or
						is no longer available.
					</p>
					<DialogFooter className="pt-2">
						<Button type="button" variant="outline" onClick={onClose}>
							Close
						</Button>
					</DialogFooter>
				</div>
			);
		}

		if (missingCoreOptions) {
			return (
				<div className="py-6 space-y-4">
					<p className="text-sm text-muted-foreground">
						Required option data couldn't be loaded. Please close and reopen the
						form or try again later.
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
			);
		}

		const readOnly = mode === "view";

		return (
			<form
				key={formKey}
				onSubmit={handleSubmit(onSubmit)}
				className="space-y-4 mt-4"
			>
				{mode !== "create" && existingGuide && (
					<p className="text-xs text-muted-foreground -mt-2">
						Last updated{" "}
						{new Date(existingGuide.last_updated).toLocaleDateString()}
					</p>
				)}
				<div className="space-y-2">
					<Label htmlFor="variety_name">{labelFor("variety_name")}</Label>
					<Controller
						name="variety_name"
						control={control}
						render={({ field }) => (
							<Input
								id="variety_name"
								{...field}
								placeholder="e.g. Roma Tomato"
								className={errors.variety_name ? "border-destructive" : ""}
								disabled={readOnly}
							/>
						)}
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
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={families}
									error={!!errors.family_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={lifecycles}
									error={!!errors.lifecycle_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
						<Label htmlFor="sow_week_start_id">
							{labelFor("sow_week_start_id")}
						</Label>
						<Controller
							name="sow_week_start_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="sow_week_start_id"
									placeholder="Select start week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.sow_week_start_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.sow_week_start_id && (
							<FormError message={errors.sow_week_start_id.message} />
						)}
					</div>

					<div className="space-y-2">
						<Label htmlFor="sow_week_end_id">
							{labelFor("sow_week_end_id")}
						</Label>
						<Controller
							name="sow_week_end_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="sow_week_end_id"
									placeholder="Select end week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.sow_week_end_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
							{labelFor("transplant_week_start_id")}
						</Label>
						<Controller
							name="transplant_week_start_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="transplant_week_start_id"
									placeholder="Select start week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.transplant_week_start_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.transplant_week_start_id && (
							<FormError message={errors.transplant_week_start_id.message} />
						)}
					</div>

					<div className="space-y-2">
						<Label htmlFor="transplant_week_end_id">
							{labelFor("transplant_week_end_id")}
						</Label>
						<Controller
							name="transplant_week_end_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="transplant_week_end_id"
									placeholder="Select end week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.transplant_week_end_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.transplant_week_end_id && (
							<FormError message={errors.transplant_week_end_id.message} />
						)}
					</div>
				</div>

				<div className="space-y-2">
					<Label htmlFor="planting_conditions_id">
						{labelFor("planting_conditions_id")}
					</Label>
					<Controller
						name="planting_conditions_id"
						control={control}
						render={({ field }) => (
							<FormSelect
								id="planting_conditions_id"
								placeholder="Select planting conditions"
								value={field.value ?? ""}
								onValueChange={field.onChange}
								options={plantingConditions}
								error={!!errors.planting_conditions_id}
								disabled={isLoadingOptions || readOnly}
								allowClear
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
							disabled={readOnly}
						/>
						{errors.soil_ph && <FormError message={errors.soil_ph.message} />}
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
							disabled={readOnly}
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
							disabled={readOnly}
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
						{...register("row_width_cm")}
						placeholder="e.g. 60"
						className={errors.row_width_cm ? "border-destructive" : ""}
						disabled={readOnly}
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
									value={field.value ?? ""}
									onValueChange={(val) => {
										field.onChange(val);
										if (val === "") {
											clearFeedFields();
										}
									}}
									options={feedTypes}
									error={!!errors.feed_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.feed_id && <FormError message={errors.feed_id.message} />}
					</div>

					<div className="space-y-2">
						<Label htmlFor="feed_week_start_id">
							{labelFor("feed_week_start_id")}
						</Label>
						<Controller
							name="feed_week_start_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="feed_week_start_id"
									placeholder="Select feed start week"
									value={field.value ?? ""}
									onValueChange={(val) => {
										field.onChange(val);
										if (val === "") {
											clearFeedFields();
										}
									}}
									options={weeks}
									error={!!errors.feed_week_start_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.feed_week_start_id && (
							<FormError message={errors.feed_week_start_id.message} />
						)}
					</div>

					<div className="space-y-2">
						<Label htmlFor="feed_frequency_id">
							{labelFor("feed_frequency_id")}
						</Label>
						<Controller
							name="feed_frequency_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="feed_frequency_id"
									placeholder="Select feed frequency"
									value={field.value ?? ""}
									onValueChange={(val) => {
										field.onChange(val);
										if (val === "") {
											clearFeedFields();
										}
									}}
									options={feedFrequencies}
									error={!!errors.feed_frequency_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.feed_frequency_id && (
							<FormError message={errors.feed_frequency_id.message} />
						)}
					</div>

					<div className="space-y-2">
						<Label htmlFor="water_frequency_id">
							{labelFor("water_frequency_id")}
						</Label>
						<Controller
							name="water_frequency_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="water_frequency_id"
									placeholder="Select water frequency"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={frequencies}
									error={!!errors.water_frequency_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
							{labelFor("high_temp_degrees")}
						</Label>
						<Input
							id="high_temp_degrees"
							type="number"
							{...register("high_temp_degrees")}
							placeholder="e.g. 30"
							className={errors.high_temp_degrees ? "border-destructive" : ""}
							disabled={readOnly}
						/>
						{errors.high_temp_degrees && (
							<FormError message={errors.high_temp_degrees.message} />
						)}
					</div>

					<div className="space-y-2">
						<Label htmlFor="high_temp_water_frequency_id">
							{labelFor("high_temp_water_frequency_id")}
						</Label>
						<Controller
							name="high_temp_water_frequency_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="high_temp_water_frequency_id"
									placeholder="Select high temp water frequency"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={frequencies}
									error={!!errors.high_temp_water_frequency_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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

				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div className="space-y-2">
						<Label htmlFor="harvest_week_start_id">
							{labelFor("harvest_week_start_id")}
						</Label>
						<Controller
							name="harvest_week_start_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="harvest_week_start_id"
									placeholder="Select harvest start week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.harvest_week_start_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.harvest_week_start_id && (
							<FormError message={errors.harvest_week_start_id.message} />
						)}
					</div>
					<div className="space-y-2">
						<Label htmlFor="harvest_week_end_id">
							{labelFor("harvest_week_end_id")}
						</Label>
						<Controller
							name="harvest_week_end_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="harvest_week_end_id"
									placeholder="Select harvest end week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.harvest_week_end_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
							{labelFor("prune_week_start_id")}
						</Label>
						<Controller
							name="prune_week_start_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="prune_week_start_id"
									placeholder="Select prune start week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.prune_week_start_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
								/>
							)}
						/>
						{errors.prune_week_start_id && (
							<FormError message={errors.prune_week_start_id.message} />
						)}
					</div>
					<div className="space-y-2">
						<Label htmlFor="prune_week_end_id">
							{labelFor("prune_week_end_id")}
						</Label>
						<Controller
							name="prune_week_end_id"
							control={control}
							render={({ field }) => (
								<FormSelect
									id="prune_week_end_id"
									placeholder="Select prune end week"
									value={field.value ?? ""}
									onValueChange={field.onChange}
									options={weeks}
									error={!!errors.prune_week_end_id}
									disabled={isLoadingOptions || readOnly}
									allowClear
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
						placeholder="Optional notes about this grow guide (minimum 5 characters)"
						className={errors.notes ? "border-destructive" : ""}
						{...register("notes")}
						disabled={readOnly}
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
								disabled={readOnly}
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
						{mode === "view" ? "Close" : "Cancel"}
					</Button>
					{mode !== "view" && (
						<Button
							type="submit"
							disabled={isSubmitting}
							className="text-white"
						>
							{submitButtonText}
						</Button>
					)}
				</DialogFooter>
			</form>
		);
	}, [
		mode,
		isLoadingOptions,
		isLoadingGuide,
		isOptionsError,
		isGuideError,
		missingCoreOptions,
		families,
		lifecycles,
		plantingConditions,
		weeks,
		frequencies,
		formKey,
		handleSubmit,
		onSubmit,
		existingGuide,
		control,
		errors,
		clearFeedFields,
		feedTypes,
		feedFrequencies,
		register,
		onClose,
		isSubmitting,
		submitButtonText,
	]);

	return (
		<Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
			<DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="text-2xl font-bold">{title}</DialogTitle>
					<DialogDescription>
						Form to create or edit a grow guide with details like variety,
						family, lifecycle, and planting conditions.
					</DialogDescription>
				</DialogHeader>

				{dialogContent}
			</DialogContent>
		</Dialog>
	);
};
