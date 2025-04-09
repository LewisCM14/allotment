import { FormError } from "@/components/FormError";
import { PageLayout } from "@/components/layouts/PageLayout";
import { Button } from "@/components/ui/Button";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/Card";
import { requestVerificationEmail } from "@/features/user/UserService";
import { useAuth } from "@/store/auth/AuthContext";
import { Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

export default function UserProfile() {
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState("");
	const [checkingStatus, setCheckingStatus] = useState(false);
	const { user, firstName } = useAuth();
	const [isEmailVerified, setIsEmailVerified] = useState(
		user?.isEmailVerified ||
		localStorage.getItem("is_email_verified") === "true",
	);

	const checkVerificationStatus = useCallback(async () => {
		const email = user?.user_email || localStorage.getItem("user_email");

		if (!email) return;

		try {
			setCheckingStatus(true);
			const response = await fetch(
				`${import.meta.env.VITE_API_URL}${import.meta.env.VITE_API_VERSION}/user/verification-status?user_email=${email}`,
				{
					method: "GET",
					headers: {
						Authorization: `Bearer ${localStorage.getItem("access_token")}`,
						"Content-Type": "application/json",
					},
				},
			);

			if (!response.ok) {
				throw new Error("Failed to fetch verification status");
			}

			const data = await response.json();

			setIsEmailVerified(data.is_email_verified);
			localStorage.setItem("is_email_verified", String(data.is_email_verified));

			if (data.is_email_verified) {
				toast.success("Email is verified!", {
					description: "You now have full access to all features",
				});
			}
		} catch (err) {
			console.error("Error checking verification status:", err);
		} finally {
			setCheckingStatus(false);
		}
	}, [user]);

	useEffect(() => {
		if (!isEmailVerified) {
			checkVerificationStatus();
		}
	}, [isEmailVerified, checkVerificationStatus]);

	const handleRequestVerification = async () => {
		const email = user?.user_email || localStorage.getItem("user_email");

		if (!email) {
			setError("User email not available");
			return;
		}

		try {
			setIsLoading(true);
			setError("");
			await requestVerificationEmail(email);
			toast.success("Verification email sent", {
				description: "Please check your inbox for the verification link",
			});
		} catch (err) {
			setError(
				err instanceof Error
					? err.message
					: "Failed to send verification email",
			);
			toast.error("Request failed", {
				description: "There was a problem sending the verification email",
			});
		} finally {
			setIsLoading(false);
		}
	};

	const userEmail =
		user?.user_email || localStorage.getItem("user_email") || "Not available";
	const userName =
		user?.user_first_name ||
		firstName ||
		localStorage.getItem("first_name") ||
		"Not provided";

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle className="text-2xl">Profile</CardTitle>
					<CardDescription>Manage your account details</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="space-y-6">
						<div className="grid gap-4">
							<div className="border-b border-border pb-2">
								<h3 className="font-medium text-muted-foreground mb-1">Name</h3>
								<p className="text-lg text-foreground">{userName}</p>
							</div>
							<div className="border-b border-border pb-2">
								<h3 className="font-medium text-muted-foreground mb-1">
									Email
								</h3>
								<p className="text-lg text-foreground">{userEmail}</p>
								{isEmailVerified && (
									<p className="text-primary text-sm mt-1">✓ Email verified</p>
								)}
							</div>
						</div>

						{error && <FormError message={error} className="mb-4" />}

						{!isEmailVerified ? (
							<div className="border border-amber-200 p-4 rounded-md bg-amber-50 dark:bg-amber-900/30 mt-6">
								<h3 className="font-medium text-amber-800 dark:text-amber-200">
									Email Not Verified
								</h3>
								<p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
									Please verify your email address to access all features.
								</p>
								<Button
									onClick={handleRequestVerification}
									disabled={isLoading}
									variant="outline"
									className="w-full"
								>
									{isLoading ? "Sending..." : "Send Verification Email"}
								</Button>
							</div>
						) : null}
					</div>
				</CardContent>
				<CardFooter className="flex justify-end">
					<Button
						variant="outline"
						size="sm"
						className="flex items-center gap-2"
						onClick={checkVerificationStatus}
						disabled={checkingStatus}
					>
						{checkingStatus ? (
							<>
								<Loader2 className="h-4 w-4 animate-spin" /> Checking...
							</>
						) : (
							<>
								<RefreshCw className="h-4 w-4" /> Refresh Status
							</>
						)}
					</Button>
				</CardFooter>
			</Card>
		</PageLayout>
	);
}
