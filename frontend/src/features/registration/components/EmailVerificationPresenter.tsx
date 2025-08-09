import { FormError } from "@/components/FormError";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { CheckCircle, Loader2, XCircle } from "lucide-react";

interface EmailVerificationPresenterProps {
	readonly isVerifying: boolean;
	readonly isSuccess: boolean;
	readonly isError: boolean;
	readonly error: Error | null;
	readonly hasNoToken: boolean;
	readonly needsPasswordReset: boolean;
	readonly onResetPassword: () => void;
	readonly onGoToDashboard: () => void;
	readonly onRequestNewVerification: () => void;
	readonly onReturnHome: () => void;
}

export default function EmailVerificationPresenter({
	isVerifying,
	isSuccess,
	isError,
	error,
	hasNoToken,
	needsPasswordReset,
	onResetPassword,
	onGoToDashboard,
	onRequestNewVerification,
	onReturnHome,
}: EmailVerificationPresenterProps) {
	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle className="text-2xl">Email Verification</CardTitle>
			</CardHeader>
			<CardContent className="flex flex-col items-center text-center">
				{/* Verifying State */}
				{isVerifying && (
					<div className="flex flex-col items-center py-8 gap-4">
						<Loader2 className="h-12 w-12 text-primary animate-spin" />
						<p className="text-foreground">Verifying your email address...</p>
					</div>
				)}

				{/* Success State */}
				{!isVerifying && isSuccess && (
					<div className="flex flex-col items-center py-8 gap-4">
						<CheckCircle className="h-16 w-16 text-primary" />
						<h2 className="text-2xl font-semibold text-primary-foreground dark:text-primary">
							Email Verified!
						</h2>
						<p className="text-muted-foreground">
							Your email address has been successfully verified. You can now
							enjoy full access to all features.
						</p>
						{needsPasswordReset ? (
							<>
								<p className="text-muted-foreground mt-2">
									Now you can proceed to reset your password.
								</p>
								<Button onClick={onResetPassword} className="mt-2">
									Reset Password
								</Button>
							</>
						) : (
							<Button onClick={onGoToDashboard} className="mt-4">
								Go to Dashboard
							</Button>
						)}
					</div>
				)}

				{/* Error State */}
				{!isVerifying && (isError || hasNoToken) && (
					<div className="flex flex-col items-center py-8 gap-4">
						<XCircle className="h-16 w-16 text-destructive" />
						<h2 className="text-2xl font-semibold text-destructive dark:text-destructive">
							Verification Failed
						</h2>
						{error && (
							<FormError
								message={
									error instanceof Error ? error.message : "Verification failed"
								}
							/>
						)}
						{hasNoToken && (
							<FormError message="No verification token provided." />
						)}
						<p className="text-muted-foreground mt-2">
							We couldn't verify your email address. The verification link may
							have expired or is invalid.
						</p>
						<div className="flex flex-col gap-2 mt-4 w-full">
							<Button onClick={onRequestNewVerification}>
								Request New Verification Link
							</Button>
							<Button variant="outline" onClick={onReturnHome}>
								Return to Home
							</Button>
						</div>
					</div>
				)}
			</CardContent>
		</Card>
	);
}
