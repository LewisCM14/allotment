import { z } from "zod";

export const userProfileSchema = z.object({
	user_first_name: z
		.string()
		.min(2, "First name must be at least 2 characters")
		.max(50, "First name cannot exceed 50 characters")
		.regex(
			/^[a-zA-Z\s-]+$/,
			"First name can only contain letters, spaces, and hyphens",
		),
	user_country_code: z
		.string()
		.length(2, "Country code must be exactly 2 characters")
		.regex(/^[A-Z]{2}$/, "Country code must be 2 uppercase letters"),
});

export type UserProfileFormData = z.infer<typeof userProfileSchema>;
