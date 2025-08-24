import { z } from "zod";

export const allotmentSchema = z.object({
	allotment_postal_zip_code: z
		.string()
		.min(5, "Postal code must be at least 5 characters")
		.max(7, "Postal code cannot exceed 7 characters")
		.refine(
			(code) => /^[a-zA-Z0-9\s]+$/.test(code),
			"Postal code must be alphanumeric (spaces allowed)",
		),
	allotment_width_meters: z
		.number({
			required_error: "Width is required",
			invalid_type_error: "Width must be a number",
		})
		.min(1.0, "Width must be at least 1 meter")
		.max(100.0, "Width cannot exceed 100 meters"),
	allotment_length_meters: z
		.number({
			required_error: "Length is required",
			invalid_type_error: "Length must be a number",
		})
		.min(1.0, "Length must be at least 1 meter")
		.max(100.0, "Length cannot exceed 100 meters"),
});

export type AllotmentFormData = z.infer<typeof allotmentSchema>;

export interface IUserAllotment {
	user_allotment_id: string;
	user_id: string;
	allotment_postal_zip_code: string;
	allotment_width_meters: number;
	allotment_length_meters: number;
}
