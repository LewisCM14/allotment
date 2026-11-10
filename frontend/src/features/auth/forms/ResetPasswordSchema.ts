import { z } from "zod";

export const resetSchema = z.object({
	email: z
		.string({ error: "Email is required" })
		.email("Please enter a valid email address"),
});

export type ResetFormData = z.infer<typeof resetSchema>;
