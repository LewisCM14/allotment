import { z } from "zod";

export const resetSchema = z.object({
    email: z
        .string()
        .email("Please enter a valid email address")
        .min(1, "Email is required"),
});

export type ResetFormData = z.infer<typeof resetSchema>;
