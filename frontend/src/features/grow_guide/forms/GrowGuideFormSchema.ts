import { z } from "zod";

// Helper: treat blank/whitespace as undefined
const emptyToUndef = (v: unknown) =>
	typeof v === "string" && v.trim() === "" ? undefined : v;

// Preprocessor for required select fields (UUID strings) so '' triggers required error
const requiredId = (fieldLabel: string) =>
	z
		.string({ required_error: `${fieldLabel} is required` })
		.transform((v) => (v === "" ? undefined : v))
		.refine((v) => !!v, { message: `${fieldLabel} is required` });

// Friendlier required number coercion
const requiredNumber = (
	fieldLabel: string,
	opts: { min?: number; max?: number },
) =>
	z
		.any()
		.transform((raw): number | undefined => {
			const v = emptyToUndef(raw);
			if (v === undefined) return undefined;
			if (typeof v === "number") return v;
			if (typeof v === "string") {
				const n = Number(v);
				return Number.isNaN(n) ? (Number.NaN as number) : n;
			}
			return Number.NaN as number;
		})
		.refine((v) => v !== undefined, { message: `${fieldLabel} is required` })
		.refine((v) => v !== undefined && !Number.isNaN(v), {
			message: `${fieldLabel} must be a valid number`,
		})
		.refine(
			(v) =>
				v === undefined ||
				((opts.min === undefined || (v as number) >= opts.min) &&
					(opts.max === undefined || (v as number) <= opts.max)),
			{
				message: `${fieldLabel} must be between ${opts.min ?? "-∞"} and ${opts.max ?? "+∞"}`,
			},
		);

// Optional number with graceful blank handling
const optionalNumber = (opts?: { min?: number; max?: number }) =>
	z
		.any()
		.transform((raw): number | undefined => {
			// Treat undefined, null, empty string, or whitespace-only as undefined
			if (raw === undefined || raw === null) return undefined;
			if (typeof raw === "string") {
				if (raw.trim() === "") return undefined;
				const n = Number(raw);
				return Number.isNaN(n) ? (Number.NaN as number) : n;
			}
			if (typeof raw === "number") return raw;
			return Number.NaN as number;
		})
		.refine((v) => v === undefined || !Number.isNaN(v), {
			message: "Must be a valid number",
		})
		.refine(
			(v) =>
				v === undefined ||
				((opts?.min === undefined || (v as number) >= (opts?.min as number)) &&
					(opts?.max === undefined || (v as number) <= (opts?.max as number))),
			{
				message: opts
					? `Must be between ${opts.min ?? "-∞"} and ${opts.max ?? "+∞"}`
					: "Out of range",
			},
		)
		.optional();

/**
 * Schema for the grow guide creation form
 * Based on the backend VarietyCreate schema
 */
const baseGrowGuideFormSchema = z.object({
	// Basic variety information
	variety_name: z
		.string()
		.transform((v) => v.trim())
		.refine((v) => v.length > 0, { message: "Variety name is required" })
		.refine((v) => v.length <= 100, {
			message: "Variety name must be less than 100 characters",
		}),
	family_id: requiredId("Plant family"),
	lifecycle_id: requiredId("Lifecycle"),

	// Sowing details (required)
	sow_week_start_id: requiredId("Sowing start week"),
	sow_week_end_id: requiredId("Sowing end week"),

	// Transplant details (optional, but must be provided together if used)
	transplant_week_start_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),
	transplant_week_end_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),

	// Planting conditions
	planting_conditions_id: requiredId("Planting conditions"),

	// Soil and spacing details (required numbers)
	soil_ph: requiredNumber("Soil pH", { min: 0, max: 14 }),
	row_width_cm: optionalNumber({ min: 1, max: 1000 }),
	plant_depth_cm: requiredNumber("Plant depth (cm)", { min: 1, max: 100 }),
	plant_space_cm: requiredNumber("Plant spacing (cm)", { min: 1, max: 1000 }),

	// Feed details (all three must be provided together)
	feed_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),
	feed_week_start_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),
	feed_frequency_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),

	// Watering details (required)
	water_frequency_id: requiredId("Watering frequency"),

	// High temperature details (required)
	high_temp_degrees: requiredNumber("High temperature threshold", {
		min: -50,
		max: 60,
	}),
	high_temp_water_frequency_id: requiredId("High temperature water frequency"),

	// Harvest details (required)
	harvest_week_start_id: requiredId("Harvest start week"),
	harvest_week_end_id: requiredId("Harvest end week"),

	// Prune details (optional, but both must be provided together)
	prune_week_start_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),
	prune_week_end_id: z
		.string()
		.optional()
		.transform((v) => (v === "" ? undefined : v)),

	// Notes (optional - allow blank string which will be stripped later)
	notes: z
		.string()
		.optional()
		.transform((val) =>
			val === undefined || val.trim() === "" ? undefined : val.trim(),
		)
		.refine((val) => val === undefined || val.length >= 5, {
			message: "Notes must be at least 5 characters or left blank",
		}),

	// Public/private setting
	is_public: z.boolean().default(false),
});

// Add validations for fields that must be provided together
const refinedGrowGuideFormSchema = baseGrowGuideFormSchema
	// Transplant weeks validation
	.refine(
		(data) => {
			if (data.transplant_week_start_id || data.transplant_week_end_id) {
				return !!data.transplant_week_start_id && !!data.transplant_week_end_id;
			}
			return true;
		},
		{
			message: "Both transplant start and end weeks must be provided together",
			path: ["transplant_week_end_id"],
		},
	)
	// Prune weeks validation
	.refine(
		(data) => {
			if (data.prune_week_start_id || data.prune_week_end_id) {
				return !!data.prune_week_start_id && !!data.prune_week_end_id;
			}
			return true;
		},
		{
			message: "Both prune start and end weeks must be provided together",
			path: ["prune_week_end_id"],
		},
	)
	// Feed trio validation (custom messages on each field)
	.superRefine((data, ctx) => {
		const anyFeed =
			data.feed_id || data.feed_week_start_id || data.feed_frequency_id;
		if (!anyFeed) return; // all empty OK
		const missing: {
			field: "feed_id" | "feed_week_start_id" | "feed_frequency_id";
			label: string;
		}[] = [];
		if (!data.feed_id) missing.push({ field: "feed_id", label: "Feed" });
		if (!data.feed_week_start_id)
			missing.push({ field: "feed_week_start_id", label: "Feed week start" });
		if (!data.feed_frequency_id)
			missing.push({ field: "feed_frequency_id", label: "Feed frequency" });
		if (missing.length === 0) return; // complete
		for (const m of missing) {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message:
					"Feed, feed week start and feed frequency must be provided together",
				path: [m.field],
			});
		}
	});
// (High temperature fields now individually required; previous pairing validation removed)

export type GrowGuideFormData = z.infer<typeof growGuideFormSchema>;
export const growGuideFormSchema = refinedGrowGuideFormSchema;
