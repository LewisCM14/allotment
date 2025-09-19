import { describe, it, expect } from "vitest";
import {
	growGuideFormSchema,
	type GrowGuideFormData,
} from "./GrowGuideFormSchema";
import type { z } from "zod";

describe("GrowGuideFormSchema", () => {
	describe("Required Fields Validation", () => {
		it("should require variety_name", () => {
			const data = {
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const varietyNameError = result.error.issues.find((issue) =>
					issue.path.includes("variety_name"),
				);
				expect(varietyNameError?.message).toContain("Required");
			}
		});

		it("should require family_id", () => {
			const data = {
				variety_name: "Test Plant",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const familyIdError = result.error.issues.find((issue) =>
					issue.path.includes("family_id"),
				);
				expect(familyIdError?.message).toContain("Plant family is required");
			}
		});

		it("should require lifecycle_id", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const lifecycleIdError = result.error.issues.find((issue) =>
					issue.path.includes("lifecycle_id"),
				);
				expect(lifecycleIdError?.message).toContain("Lifecycle is required");
			}
		});

		it("should require soil_ph", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				plant_depth_cm: 2,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const soilPhError = result.error.issues.find((issue) =>
					issue.path.includes("soil_ph"),
				);
				expect(soilPhError?.message).toContain("Soil pH is required");
			}
		});

		it("should require plant_depth_cm", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				soil_ph: 6.5,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const plantDepthError = result.error.issues.find((issue) =>
					issue.path.includes("plant_depth_cm"),
				);
				expect(plantDepthError?.message).toContain(
					"Plant depth (cm) is required",
				);
			}
		});

		it("should require plant_space_cm", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				high_temp_degrees: 25,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const plantSpaceError = result.error.issues.find((issue) =>
					issue.path.includes("plant_space_cm"),
				);
				expect(plantSpaceError?.message).toContain(
					"Plant spacing (cm) is required",
				);
			}
		});

		it("should require high_temp_degrees", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				is_public: false,
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const highTempError = result.error.issues.find((issue) =>
					issue.path.includes("high_temp_degrees"),
				);
				expect(highTempError?.message).toContain(
					"High temperature threshold is required",
				);
			}
		});

		it("should have default value for is_public when not provided", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
			} as Partial<GrowGuideFormData>;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.is_public).toBe(false);
			}
		});
	});

	describe("String Field Validation", () => {
		it("should reject empty variety_name", () => {
			const data = {
				variety_name: "",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const varietyNameError = result.error.issues.find((issue) =>
					issue.path.includes("variety_name"),
				);
				expect(varietyNameError?.message).toContain("Variety name is required");
			}
		});

		it("should reject whitespace-only variety_name", () => {
			const data = {
				variety_name: "   ",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const varietyNameError = result.error.issues.find((issue) =>
					issue.path.includes("variety_name"),
				);
				expect(varietyNameError?.message).toContain("Variety name is required");
			}
		});

		it("should accept valid variety_name", () => {
			const data = {
				variety_name: "Cherry Tomato",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.variety_name).toBe("Cherry Tomato");
			}
		});

		it("should handle empty string ID fields by transforming to undefined", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const familyIdError = result.error.issues.find((issue) =>
					issue.path.includes("family_id"),
				);
				expect(familyIdError?.message).toContain("Plant family is required");
			}
		});
	});

	describe("Number Field Validation", () => {
		it("should validate soil_ph range (0-14)", () => {
			const baseData = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// Test valid pH
			const validResult = growGuideFormSchema.safeParse({
				...baseData,
				soil_ph: 6.5,
			});
			expect(validResult.success).toBe(true);

			// Test pH too low
			const lowResult = growGuideFormSchema.safeParse({
				...baseData,
				soil_ph: -0.5,
			});
			expect(lowResult.success).toBe(false);
			if (!lowResult.success) {
				const phError = lowResult.error.issues.find((issue) =>
					issue.path.includes("soil_ph"),
				);
				expect(phError?.message).toContain("between 0 and 14");
			}

			// Test pH too high
			const highResult = growGuideFormSchema.safeParse({
				...baseData,
				soil_ph: 15,
			});
			expect(highResult.success).toBe(false);
			if (!highResult.success) {
				const phError = highResult.error.issues.find((issue) =>
					issue.path.includes("soil_ph"),
				);
				expect(phError?.message).toContain("between 0 and 14");
			}
		});

		it("should validate plant_depth_cm minimum (1)", () => {
			const baseData = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// Test valid depth
			const validResult = growGuideFormSchema.safeParse({
				...baseData,
				plant_depth_cm: 2.5,
			});
			expect(validResult.success).toBe(true);

			// Test depth too low
			const lowResult = growGuideFormSchema.safeParse({
				...baseData,
				plant_depth_cm: 0.5,
			});
			expect(lowResult.success).toBe(false);
			if (!lowResult.success) {
				const depthError = lowResult.error.issues.find((issue) =>
					issue.path.includes("plant_depth_cm"),
				);
				expect(depthError?.message).toContain("between 1 and");
			}
		});

		it("should validate plant_space_cm minimum (1)", () => {
			const baseData = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// Test valid spacing
			const validResult = growGuideFormSchema.safeParse({
				...baseData,
				plant_space_cm: 30,
			});
			expect(validResult.success).toBe(true);

			// Test spacing too low
			const lowResult = growGuideFormSchema.safeParse({
				...baseData,
				plant_space_cm: 0.5,
			});
			expect(lowResult.success).toBe(false);
			if (!lowResult.success) {
				const spaceError = lowResult.error.issues.find((issue) =>
					issue.path.includes("plant_space_cm"),
				);
				expect(spaceError?.message).toContain("between 1 and");
			}
		});

		it("should validate high_temp_degrees range (-50 to 60)", () => {
			const baseData = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// Test valid temperature
			const validResult = growGuideFormSchema.safeParse({
				...baseData,
				high_temp_degrees: 25,
			});
			expect(validResult.success).toBe(true);

			// Test temperature too low
			const lowResult = growGuideFormSchema.safeParse({
				...baseData,
				high_temp_degrees: -60,
			});
			expect(lowResult.success).toBe(false);
			if (!lowResult.success) {
				const tempError = lowResult.error.issues.find((issue) =>
					issue.path.includes("high_temp_degrees"),
				);
				expect(tempError?.message).toContain("between -50 and 60");
			}

			// Test temperature too high
			const highResult = growGuideFormSchema.safeParse({
				...baseData,
				high_temp_degrees: 70,
			});
			expect(highResult.success).toBe(false);
			if (!highResult.success) {
				const tempError = highResult.error.issues.find((issue) =>
					issue.path.includes("high_temp_degrees"),
				);
				expect(tempError?.message).toContain("between -50 and 60");
			}
		});

		it("should handle string numbers correctly", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: "6.5",
				plant_depth_cm: "2.5",
				plant_space_cm: "30",
				water_frequency_id: "freq-1",
				high_temp_degrees: "25",
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(typeof result.data.soil_ph).toBe("number");
				expect(result.data.soil_ph).toBe(6.5);
				expect(typeof result.data.plant_depth_cm).toBe("number");
				expect(result.data.plant_depth_cm).toBe(2.5);
			}
		});

		it("should reject invalid number strings", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: "not-a-number",
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const phError = result.error.issues.find((issue) =>
					issue.path.includes("soil_ph"),
				);
				expect(phError?.message).toContain("valid number");
			}
		});

		it("should handle empty string numbers", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: "",
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				const phError = result.error.issues.find((issue) =>
					issue.path.includes("soil_ph"),
				);
				expect(phError?.message).toContain("Soil pH is required");
			}
		});
	});

	describe("Optional Field Validation", () => {
		it("should accept undefined optional fields", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
				// Optional fields not provided
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
		});

		it("should accept valid optional row_width_cm", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				row_width_cm: 40,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.row_width_cm).toBe(40);
			}
		});

		it("should validate optional row_width_cm range", () => {
			const baseData = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// Test row_width_cm too low
			const lowResult = growGuideFormSchema.safeParse({
				...baseData,
				row_width_cm: 0.5,
			});
			expect(lowResult.success).toBe(false);
			if (!lowResult.success) {
				const rowWidthError = lowResult.error.issues.find((issue) =>
					issue.path.includes("row_width_cm"),
				);
				expect(rowWidthError?.message).toContain("between 1 and");
			}
		});

		it("should handle empty string for optional notes", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				notes: "",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.notes).toBeUndefined();
			}
		});

		it("should handle whitespace-only notes", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				notes: "   ",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.notes).toBeUndefined();
			}
		});
	});

	describe("Boolean Field Validation", () => {
		it("should accept true for is_public", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: true,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.is_public).toBe(true);
			}
		});

		it("should accept false for is_public", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.is_public).toBe(false);
			}
		});
	});

	describe("Complex Validation Scenarios", () => {
		it("should validate complete valid form data", () => {
			const data: GrowGuideFormData = {
				variety_name: "Cherry Tomato",
				family_id: "solanaceae",
				lifecycle_id: "annual",
				sow_week_start_id: "week-10",
				sow_week_end_id: "week-12",
				transplant_week_start_id: "week-14",
				transplant_week_end_id: "week-16",
				planting_conditions_id: "indoors",
				soil_ph: 6.5,
				plant_depth_cm: 2.5,
				plant_space_cm: 45,
				row_width_cm: 60,
				feed_id: "tomato-feed",
				feed_week_start_id: "week-18",
				feed_frequency_id: "weekly",
				water_frequency_id: "daily",
				high_temp_degrees: 30,
				high_temp_water_frequency_id: "twice-daily",
				harvest_week_start_id: "week-24",
				harvest_week_end_id: "week-36",
				prune_week_start_id: "week-20",
				prune_week_end_id: "week-32",
				notes: "Excellent variety for containers and small gardens.",
				is_public: true,
			};

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.variety_name).toBe("Cherry Tomato");
				expect(result.data.soil_ph).toBe(6.5);
				expect(result.data.is_public).toBe(true);
				expect(result.data.notes).toBe(
					"Excellent variety for containers and small gardens.",
				);
			}
		});

		it("should validate minimal required data", () => {
			const data: Partial<GrowGuideFormData> = {
				variety_name: "Minimal Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 7.0,
				plant_depth_cm: 1.0,
				plant_space_cm: 10,
				water_frequency_id: "freq-1",
				high_temp_degrees: 20,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-15",
				harvest_week_end_id: "week-20",
				is_public: false,
			};

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
		});

		it("should fail with multiple validation errors", () => {
			const data = {
				variety_name: "",
				family_id: "",
				soil_ph: -1,
				plant_depth_cm: 0,
				plant_space_cm: 0,
				high_temp_degrees: 100,
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
			if (!result.success) {
				expect(result.error.issues.length).toBeGreaterThan(1);

				const errorPaths = result.error.issues.map((issue) => issue.path[0]);
				expect(errorPaths).toContain("variety_name");
				expect(errorPaths).toContain("family_id");
				expect(errorPaths).toContain("soil_ph");
				expect(errorPaths).toContain("plant_depth_cm");
				expect(errorPaths).toContain("plant_space_cm");
				expect(errorPaths).toContain("high_temp_degrees");
			}
		});

		it("should transform and validate mixed data types", () => {
			const data = {
				variety_name: "Mixed Types Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: "6.8", // string number
				plant_depth_cm: 2.5, // actual number
				plant_space_cm: "30", // string number
				water_frequency_id: "freq-1",
				high_temp_degrees: "25", // string number
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-25",
				row_width_cm: "", // empty string (optional)
				notes: "   Test notes   ", // string with whitespace
				is_public: false,
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(typeof result.data.soil_ph).toBe("number");
				expect(result.data.soil_ph).toBe(6.8);
				expect(typeof result.data.plant_space_cm).toBe("number");
				expect(result.data.plant_space_cm).toBe(30);
				expect(result.data.row_width_cm).toBeUndefined();
				expect(result.data.notes).toBe("Test notes");
			}
		});
	});

	describe("Edge Cases", () => {
		it("should handle null values", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
				notes: null,
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
			if (result.success) {
				expect(result.data.notes).toBeUndefined();
			}
		});

		it("should handle undefined values for optional fields", () => {
			const data = {
				variety_name: "Test Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
				transplant_week_start_id: undefined,
				transplant_week_end_id: undefined,
				feed_id: undefined,
				notes: undefined,
			} as GrowGuideFormData;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
		});

		it("should reject invalid data types", () => {
			const data = {
				variety_name: 123, // number instead of string
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				soil_ph: "not-a-number",
				plant_depth_cm: 2,
				plant_space_cm: 30,
				high_temp_degrees: 25,
				is_public: "yes", // string instead of boolean
			} as unknown;

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(false);
		});

		it("should handle extreme but valid values", () => {
			const data: GrowGuideFormData = {
				variety_name: "Extreme Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 0, // minimum pH
				plant_depth_cm: 1, // minimum depth
				plant_space_cm: 1, // minimum spacing
				water_frequency_id: "freq-1",
				high_temp_degrees: -50, // minimum temperature
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
		});

		it("should handle maximum valid values", () => {
			const data: GrowGuideFormData = {
				variety_name: "Maximum Plant",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 14.0, // maximum pH
				plant_depth_cm: 100, // max depth
				plant_space_cm: 1000, // max spacing
				water_frequency_id: "freq-1",
				high_temp_degrees: 60, // maximum temperature
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: true,
			};

			const result = growGuideFormSchema.safeParse(data);

			expect(result.success).toBe(true);
		});
	});

	describe("Type Safety", () => {
		it("should export correct TypeScript type", () => {
			const data: GrowGuideFormData = {
				variety_name: "Type Safety Test",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// This should compile without errors if types are correct
			expect(data.variety_name).toBe("Type Safety Test");
			expect(typeof data.soil_ph).toBe("number");
			expect(typeof data.is_public).toBe("boolean");
		});

		it("should infer correct output type from schema", () => {
			type SchemaOutput = z.infer<typeof growGuideFormSchema>;

			const data: SchemaOutput = {
				variety_name: "Schema Output Test",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
			};

			// This should match GrowGuideFormData type
			expect(data.variety_name).toBe("Schema Output Test");
		});
	});
});
