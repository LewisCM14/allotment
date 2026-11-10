import { z } from "zod";

const requiredString = (message: string) =>
	z.preprocess(
		(value) => (value === "" ? undefined : value),
		z.string({ error: message }),
	);

export const loginSchema = z.object({
	email: requiredString("Email is required")
		.pipe(z.string().trim().email("Invalid email"))
		.transform((s) => s.toLowerCase()),
	password: requiredString("Password is required").pipe(
		z.string().min(1, "Password is required"),
	),
});

export type LoginFormData = z.infer<typeof loginSchema>;
