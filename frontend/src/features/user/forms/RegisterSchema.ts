import { z } from "zod";

export const registerSchema = z
	.object({
		email: z.string().email("Invalid email"),
		password: z
			.string()
			.min(8, "Password must be at least 8 characters long")
			.max(30, "Password cannot exceed 30 characters")
			.refine(
				(password) => /[A-Z]/.test(password),
				"Password must contain at least one uppercase letter",
			)
			.refine(
				(password) => /\d/.test(password),
				"Password must contain at least one number",
			)
			.refine(
				(password) => /[!"#$%&'()*+,-./:;<=>?@[\\\]^_`{|}~]/.test(password),
				"Password must contain at least one special character",
			),
		password_confirm: z.string().min(1, "Please confirm your password"),
		first_name: z
			.string()
			.min(2, "First name must be at least 2 characters")
			.max(50, "First name cannot exceed 50 characters")
			.refine(
				(name) => /^[a-zA-Z]+(?:[- ][a-zA-Z]+)*$/.test(name),
				"First name can only contain letters, spaces, and hyphens",
			),
		country_code: z
			.string()
			.length(2, "Country code must be exactly 2 characters")
			.transform((val) => val.toUpperCase()),
	})
	.refine((data) => data.password === data.password_confirm, {
		message: "Passwords do not match",
		path: ["password_confirm"],
	});

export type RegisterFormData = z.infer<typeof registerSchema>;
