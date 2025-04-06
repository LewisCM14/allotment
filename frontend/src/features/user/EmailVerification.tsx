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

	useEffect(() => {
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
	}, [token]);

	return (
		<PageLayout variant="default">
			<Card className="w-full max-w-md mx-auto">
				<CardHeader>
					<CardTitle>Email Verification</CardTitle>
				</CardHeader>
				<CardContent className="flex flex-col items-center text-center">
					{verifying && (
						<div className="flex flex-col items-center py-8 gap-4">
							<Loader2 className="h-12 w-12 text-primary animate-spin" />
							<p>Verifying your email address...</p>
						</div>
					)}

					{!verifying && success && (
						<div className="flex flex-col items-center py-8 gap-4">
							<CheckCircle className="h-16 w-16 text-green-500" />
							<h2 className="text-2xl font-semibold text-green-700">
								Email Verified!
							</h2>
							<p className="text-gray-600">
								Your email address has been successfully verified. You can now
								enjoy full access to all features.
							</p>
							<Button onClick={() => navigate("/")} className="mt-4">
								Go to Dashboard
							</Button>
						</div>
					)}

					{!verifying && !success && (
						<div className="flex flex-col items-center py-8 gap-4">
							<XCircle className="h-16 w-16 text-red-500" />
							<h2 className="text-2xl font-semibold text-red-700">
								Verification Failed
							</h2>
							{error && <FormError message={error} />}
							<p className="text-gray-600 mt-2">
								We couldn't verify your email address. The verification link may
								have expired or is invalid.
							</p>
							<div className="flex flex-col gap-2 mt-4 w-full">
								<Button asChild>
									<Link to="/request-verification">
										Request New Verification Link
									</Link>
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
