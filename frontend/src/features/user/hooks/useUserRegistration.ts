import { useMutation } from "@tanstack/react-query";
import { registerUser } from "../services/UserService";

/**
 * Hook to handle user registration
 */
export const useUserRegistration = () => {
	return useMutation({
		mutationFn: ({
			email,
			password,
			firstName,
			countryCode,
		}: {
			email: string;
			password: string;
			firstName: string;
			countryCode: string;
		}) => registerUser(email, password, firstName, countryCode),
		retry: (failureCount, error) => {
			// Don't retry on validation errors or duplicate email
			if (
				error?.message?.includes("already exists") ||
				error?.message?.includes("validation") ||
				error?.message?.includes("400")
			) {
				return false;
			}
			return failureCount < 1; // Only retry once for network errors
		},
	});
};
