import { describe, it, expect } from "vitest";
import { registerSchema } from "./RegisterSchema";

describe("registerSchema", () => {
	it("normalizes email to lowercase and trims", () => {
		const input = {
			email: "  TeSt@ExAmPlE.CoM  ",
			password: "Password1!",
			password_confirm: "Password1!",
			first_name: "John",
			country_code: "gb",
		};

		const parsed = registerSchema.parse(input);
		expect(parsed.email).toBe("test@example.com");
		expect(parsed.country_code).toBe("GB");
	});

	it("fails when passwords do not match", () => {
		const input = {
			email: "user@example.com",
			password: "Password1!",
			password_confirm: "Password2!",
			first_name: "John",
			country_code: "GB",
		};

		const result = registerSchema.safeParse(input);
		expect(result.success).toBe(false);
	});
});
