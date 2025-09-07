import { z } from "zod";

// Base validation rules
const uuidSchema = z.string().uuid("Invalid ID format");
const nameSchema = z.string().min(1, "Name is required").max(100, "Name must be less than 100 characters");
const weekIdSchema = z.string().min(1, "Week selection is required");
const phSchema = z.number().min(0, "pH must be positive").max(14, "pH cannot exceed 14");
const depthSchema = z.number().min(0.1, "Depth must be at least 0.1cm").max(100, "Depth cannot exceed 100cm");
const spacingSchema = z.number().min(1, "Spacing must be at least 1cm").max(1000, "Spacing cannot exceed 1000cm");

// Create variety schema
export const createVarietySchema = z.object({
	variety_name: nameSchema,
	family_id: uuidSchema,
	lifecycle_id: uuidSchema,
	sow_week_start_id: weekIdSchema,
	sow_week_end_id: weekIdSchema,
	planting_conditions_id: uuidSchema,
	soil_ph: phSchema.optional(),
	plant_depth_cm: depthSchema.optional(),
	plant_space_cm: spacingSchema.optional(),
	water_frequency_id: uuidSchema.optional(),
	high_temp_water_frequency_id: uuidSchema.optional(),
	harvest_week_start_id: weekIdSchema.optional(),
	harvest_week_end_id: weekIdSchema.optional(),
	feed_frequency_id: uuidSchema.optional(),
	feed_id: uuidSchema.optional(),
}).refine(
	(data) => {
		// If harvest weeks are provided, start should be before or equal to end
		if (data.harvest_week_start_id && data.harvest_week_end_id) {
			// For now, we'll assume week IDs are comparable (this might need adjustment based on actual week ID format)
			return data.harvest_week_start_id <= data.harvest_week_end_id;
		}
		return true;
	},
	{
		message: "Harvest start week must be before or equal to harvest end week",
		path: ["harvest_week_end_id"],
	}
).refine(
	(data) => {
		// Sow end week should be after or equal to sow start week
		return data.sow_week_start_id <= data.sow_week_end_id;
	},
	{
		message: "Sow end week must be after or equal to sow start week",
		path: ["sow_week_end_id"],
	}
);

// Update variety schema (all fields optional except those that shouldn't be changed)
export const updateVarietySchema = z.object({
	variety_name: nameSchema.optional(),
	family_id: uuidSchema.optional(),
	lifecycle_id: uuidSchema.optional(),
	sow_week_start_id: weekIdSchema.optional(),
	sow_week_end_id: weekIdSchema.optional(),
	planting_conditions_id: uuidSchema.optional(),
	soil_ph: phSchema.optional(),
	plant_depth_cm: depthSchema.optional(),
	plant_space_cm: spacingSchema.optional(),
	water_frequency_id: uuidSchema.optional(),
	high_temp_water_frequency_id: uuidSchema.optional(),
	harvest_week_start_id: weekIdSchema.optional(),
	harvest_week_end_id: weekIdSchema.optional(),
	feed_frequency_id: uuidSchema.optional(),
	feed_id: uuidSchema.optional(),
}).refine(
	(data) => {
		// If both harvest weeks are provided, validate order
		if (data.harvest_week_start_id && data.harvest_week_end_id) {
			return data.harvest_week_start_id <= data.harvest_week_end_id;
		}
		return true;
	},
	{
		message: "Harvest start week must be before or equal to harvest end week",
		path: ["harvest_week_end_id"],
	}
).refine(
	(data) => {
		// If both sow weeks are provided, validate order
		if (data.sow_week_start_id && data.sow_week_end_id) {
			return data.sow_week_start_id <= data.sow_week_end_id;
		}
		return true;
	},
	{
		message: "Sow end week must be after or equal to sow start week",
		path: ["sow_week_end_id"],
	}
);

// Water days schema for updating watering schedule
export const waterDaysSchema = z.object({
	water_days: z.array(z.string().regex(/^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$/, "Invalid day")).min(1, "At least one day must be selected"),
});

// Type inference from schemas
export type CreateVarietyFormData = z.infer<typeof createVarietySchema>;
export type UpdateVarietyFormData = z.infer<typeof updateVarietySchema>;
export type WaterDaysFormData = z.infer<typeof waterDaysSchema>;
