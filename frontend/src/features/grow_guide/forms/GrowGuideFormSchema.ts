import { z } from "zod";

/**
 * Schema for the grow guide creation form
 * Based on the backend VarietyCreate schema
 */
const baseGrowGuideFormSchema = z.object({
	// Basic variety information
	variety_name: z
		.string()
		.min(1, { message: "Variety name is required" })
		.max(100, { message: "Variety name must be less than 100 characters" }),
	family_id: z.string({ required_error: "Please select a plant family" }),
	lifecycle_id: z.string({ required_error: "Please select a lifecycle" }),

	// Sowing details (required)
	sow_week_start_id: z.string({
		required_error: "Please select a sowing start week",
	}),
	sow_week_end_id: z.string({
		required_error: "Please select a sowing end week",
	}),

	// Transplant details (optional, but must be provided together if used)
	transplant_week_start_id: z.string().optional(),
	transplant_week_end_id: z.string().optional(),

	// Planting conditions
	planting_conditions_id: z.string({
		required_error: "Please select planting conditions",
	}),

	// Soil and spacing details
	soil_ph: z
		.number()
		.min(0, { message: "Soil pH must be between 0 and 14" })
		.max(14, { message: "Soil pH must be between 0 and 14" }),
	row_width_cm: z
		.number()
		.min(1, { message: "Row width must be at least 1 cm" })
		.max(1000, { message: "Row width must be less than 1000 cm" })
		.optional(),
	plant_depth_cm: z
		.number()
		.min(1, { message: "Plant depth must be at least 1 cm" })
		.max(100, { message: "Plant depth must be less than 100 cm" }),
	plant_space_cm: z
		.number()
		.min(1, { message: "Plant spacing must be at least 1 cm" })
		.max(1000, { message: "Plant spacing must be less than 1000 cm" }),

	// Feed details (all three must be provided together)
	feed_id: z.string().optional(),
	feed_week_start_id: z.string().optional(),
	feed_frequency_id: z.string().optional(),

	// Watering details (required)
	water_frequency_id: z.string({
		required_error: "Please select a watering frequency",
	}),

	// High temperature details (optional, but both must be provided together)
	high_temp_degrees: z
		.number()
		.min(-50, { message: "High temperature must be at least -50 degrees" })
		.max(60, { message: "High temperature must be less than 60 degrees" })
		.optional(),
	high_temp_water_frequency_id: z.string().optional(),

	// Harvest details (required)
	harvest_week_start_id: z.string({
		required_error: "Please select a harvest start week",
	}),
	harvest_week_end_id: z.string({
		required_error: "Please select a harvest end week",
	}),

	// Prune details (optional, but both must be provided together)
	prune_week_start_id: z.string().optional(),
	prune_week_end_id: z.string().optional(),

	// Notes (optional)
	notes: z.string().min(5).max(500).optional(),

	// Public/private setting
	is_public: z.boolean().default(false),
});

// Add validations for fields that must be provided together
const refinedGrowGuideFormSchema = baseGrowGuideFormSchema
	// Transplant weeks validation
	.refine(
		(data) => {
			// If one transplant week is provided, both must be provided
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
	// Feed details validation
	.refine(
		(data) => {
			// If any feed detail is provided, all three must be provided
			const hasAnyFeedDetail =
				data.feed_id || data.feed_week_start_id || data.feed_frequency_id;
			if (hasAnyFeedDetail) {
				return (
					!!data.feed_id &&
					!!data.feed_week_start_id &&
					!!data.feed_frequency_id
				);
			}
			return true;
		},
		{
			message:
				"Feed ID, feed week start, and feed frequency must all be provided together",
			path: ["feed_id"],
		},
	)
	// High temperature validation
	.refine(
		(data) => {
			// If high temp degrees is provided, high temp water frequency must also be provided
			if (data.high_temp_degrees !== undefined) {
				return !!data.high_temp_water_frequency_id;
			}
			return true;
		},
		{
			message:
				"High temperature water frequency must be provided when high temperature is specified",
			path: ["high_temp_water_frequency_id"],
		},
	)
	// Prune weeks validation
	.refine(
		(data) => {
			// If one prune week is provided, both must be provided
			if (data.prune_week_start_id || data.prune_week_end_id) {
				return !!data.prune_week_start_id && !!data.prune_week_end_id;
			}
			return true;
		},
		{
			message: "Both prune start and end weeks must be provided together",
			path: ["prune_week_end_id"],
		},
	);

export type GrowGuideFormData = z.infer<typeof growGuideFormSchema>;
export const growGuideFormSchema = refinedGrowGuideFormSchema;
