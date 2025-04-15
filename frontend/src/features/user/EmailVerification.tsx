import { FormError } from "@/components/FormError";
import { PageLayout } from "@/components/layouts/PageLayout";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { verifyEmail } from "@/features/user/UserService";
import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

export default function EmailVerificationPage() {
	const [searchParams] = useSearchParams();
	const token = searchParams.get("token");
	const [verifying, setVerifying] = useState(true);
	const [success, setSuccess] = useState(false);
	const [error, setError] = useState("");
	const navigate = useNavigate();
	const [needsPasswordReset, setNeedsPasswordReset] = useState(false);

	useEffect(() => {
		const fromReset = searchParams.get("fromReset") === "true";
		setNeedsPasswordReset(fromReset);

		async function verifyUserEmail() {
			if (!token) {
				setVerifying(false);
				setSuccess(false);
				setError("No verification token provided.");
				return;
			}

			try {
				setVerifying(true);
				await verifyEmail(token);
				setSuccess(true);
				setError("");
				localStorage.setItem("is_email_verified", "true");
				toast.success("Email verified successfully", {
					description:
						"Your email has been verified. You can now access all features.",
				});
			} catch (err: unknown) {
				setSuccess(false);
				setError(
					err instanceof Error
						? err.message
						: "Failed to verify email. Please try again.",
				);
				toast.error("Verification failed", {
					description: "There was a problem verifying your email address.",
				});
			} finally {
				setVerifying(false);
			}
		}

		verifyUserEmail();
	}, [token, searchParams]);

	const handleResetPassword = () => {
		navigate("/reset-password");
	};

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle className="text-2xl">Email Verification</CardTitle>
				</CardHeader>
				<CardContent className="flex flex-col items-center text-center">
					{verifying && (
						<div className="flex flex-col items-center py-8 gap-4">
							<Loader2 className="h-12 w-12 text-primary animate-spin" />
							<p className="text-foreground">Verifying your email address...</p>
						</div>
					)}

					{!verifying && success && (
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
									<Button onClick={handleResetPassword} className="mt-2">
										Reset Password
									</Button>
								</>
							) : (
								<Button onClick={() => navigate("/")} className="mt-4">
									Go to Dashboard
								</Button>
							)}
						</div>
					)}

					{!verifying && !success && (
						<div className="flex flex-col items-center py-8 gap-4">
							<XCircle className="h-16 w-16 text-destructive" />
							<h2 className="text-2xl font-semibold text-destructive dark:text-destructive">
								Verification Failed
							</h2>
							{error && <FormError message={error} />}
							<p className="text-muted-foreground mt-2">
								We couldn't verify your email address. The verification link may
								have expired or is invalid.
							</p>
							<div className="flex flex-col gap-2 mt-4 w-full">
								<Button asChild>
									<Link to="/profile">Request New Verification Link</Link>
								</Button>
								<Button variant="outline" asChild>
									<Link to="/">Return to Home</Link>
								</Button>
							</div>
						</div>
					)}
				</CardContent>
			</Card>
		</PageLayout>
	);
}
