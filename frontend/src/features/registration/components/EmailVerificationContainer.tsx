import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useEmailVerification } from "../hooks/useEmailVerification";
import EmailVerificationPresenter from "./EmailVerificationPresenter";

export default function EmailVerificationContainer() {
	const [searchParams] = useSearchParams();
	const token = searchParams.get("token");
	const navigate = useNavigate();

	const [needsPasswordReset, setNeedsPasswordReset] = useState(false);
	const [hasAttemptedVerification, setHasAttemptedVerification] =
		useState(false);

	const emailVerificationMutation = useEmailVerification();

	useEffect(() => {
		const fromReset = searchParams.get("fromReset") === "true";
		setNeedsPasswordReset(fromReset);
	}, [searchParams]);

	useEffect(() => {
		if (token && !hasAttemptedVerification) {
			setHasAttemptedVerification(true);

			emailVerificationMutation.mutate(
				{ token, needsPasswordReset },
				{
					onSuccess: () => {
						toast.success("Email verified successfully", {
							description: needsPasswordReset
								? "Your email has been verified. You can now reset your password."
								: "Your email has been verified. You can now access all features.",
						});
					},
					onError: () => {
						toast.error("Verification failed", {
							description: "There was a problem verifying your email address.",
						});
					},
				},
			);
		}
	}, [
		token,
		hasAttemptedVerification,
		needsPasswordReset,
		emailVerificationMutation,
	]);

	const handleResetPassword = () => {
		navigate("/reset-password");
	};

	const handleGoToDashboard = () => {
		navigate("/");
	};

	const handleRequestNewVerification = () => {
		navigate("/profile");
	};

	const handleReturnHome = () => {
		navigate("/");
	};

	// Derive state for presenter
	const isVerifying = emailVerificationMutation.isPending;
	const isSuccess = emailVerificationMutation.isSuccess;
	const isError = emailVerificationMutation.isError;
	const error = emailVerificationMutation.error;
	const hasNoToken = !token;

	return (
		<EmailVerificationPresenter
			isVerifying={isVerifying}
			isSuccess={isSuccess}
			isError={isError}
			error={error}
			hasNoToken={hasNoToken}
			needsPasswordReset={needsPasswordReset}
			onResetPassword={handleResetPassword}
			onGoToDashboard={handleGoToDashboard}
			onRequestNewVerification={handleRequestNewVerification}
			onReturnHome={handleReturnHome}
		/>
	);
}
