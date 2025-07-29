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
import { Loader2, RefreshCw } from "lucide-react";

interface UserProfilePresenterProps {
	readonly userName: string;
	readonly userEmail: string;
	readonly isEmailVerified: boolean;
	readonly isLoading: boolean;
	readonly isRefreshing: boolean;
	readonly error?: string;
	readonly onRequestVerification: () => void;
	readonly onRefreshStatus: () => void;
}

export default function UserProfilePresenter({
	userName,
	userEmail,
	isEmailVerified,
	isLoading,
	isRefreshing,
	error,
	onRequestVerification,
	onRefreshStatus,
}: UserProfilePresenterProps) {
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

						{!isEmailVerified && (
							<div className="border border-amber-200 p-4 rounded-md bg-amber-50 dark:bg-amber-900/30 mt-6">
								<h3 className="font-medium text-amber-800 dark:text-amber-200">
									Email Not Verified
								</h3>
								<p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
									Please verify your email address to access all features.
								</p>
								<Button
									onClick={onRequestVerification}
									disabled={isLoading}
									variant="outline"
									className="w-full"
								>
									{isLoading ? "Sending..." : "Send Verification Email"}
								</Button>
							</div>
						)}
					</div>
				</CardContent>
				<CardFooter className="flex justify-end">
					<Button
						variant="outline"
						size="sm"
						className="flex items-center gap-2"
						onClick={onRefreshStatus}
						disabled={isRefreshing}
					>
						{isRefreshing ? (
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
