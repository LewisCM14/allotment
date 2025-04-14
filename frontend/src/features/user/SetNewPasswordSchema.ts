import { z } from "zod";

export const setNewPasswordSchema = z
	.object({
		password: z
			.string()
			.min(8, "Password must be at least 8 characters long")
			.max(30, "Password cannot exceed 30 characters")
			.refine(
				(password) => /[A-Z]/.test(password),
				"Password must contain at least one uppercase letter",
			)
			.refine(
				(password) => /[0-9]/.test(password),
				"Password must contain at least one number",
			)
			.refine(
				(password) => /[!@#$%^&*\(\)-_=+\[\]{}|;:'",.\\<>\/?`~]/.test(password),
				"Password must contain at least one special character",
			),
		password_confirm: z.string().min(1, "Please confirm your password"),
	})
	.refine((data) => data.password === data.password_confirm, {
		message: "Passwords do not match",
		path: ["password_confirm"],
	});

export type SetNewPasswordFormData = z.infer<typeof setNewPasswordSchema>;
