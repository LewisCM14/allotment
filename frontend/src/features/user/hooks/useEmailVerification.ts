import { useMutation, useQuery } from "@tanstack/react-query";
import { verifyEmail } from "../services/UserService";

// Query key factory for email verification
export const emailVerificationKeys = {
	all: ["email-verification"] as const,
	verify: (token: string) =>
		[...emailVerificationKeys.all, "verify", token] as const,
};

/**
 * Hook to verify email with token
 * This is a one-time operation, so we use a mutation rather than a query
 */
export const useEmailVerification = () => {
	return useMutation({
		mutationFn: ({
			token,
			needsPasswordReset,
		}: { token: string; needsPasswordReset: boolean }) =>
			verifyEmail(token, needsPasswordReset),
		onSuccess: () => {
			// Update local storage to indicate email is verified
			localStorage.setItem("is_email_verified", "true");
		},
		onError: () => {
			// Clear any stale verification status
			localStorage.removeItem("is_email_verified");
		},
		retry: (failureCount, error) => {
			// Don't retry on token-related errors (expired, invalid)
			if (
				error?.message?.includes("token") ||
				error?.message?.includes("expired")
			) {
				return false;
			}
			return failureCount < 1; // Only retry once for network errors
		},
	});
};
