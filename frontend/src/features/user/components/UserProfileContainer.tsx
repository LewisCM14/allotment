import { useAuth } from "@/store/auth/AuthContext";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
	useEmailVerificationStatus,
	useRequestEmailVerification,
	useRefreshVerificationStatus,
} from "../hooks/useUserProfile";
import UserProfilePresenter from "./UserProfilePresenter";

export default function UserProfileContainer() {
	const { user, firstName } = useAuth();
	const [localVerificationStatus, setLocalVerificationStatus] = useState(
		user?.isEmailVerified ??
			localStorage.getItem("is_email_verified") === "true",
	);

	const {
		data: verificationData,
		isLoading: isCheckingStatus,
		error: verificationError,
	} = useEmailVerificationStatus(user?.user_email);

	const requestVerificationMutation = useRequestEmailVerification();
	const refreshStatusMutation = useRefreshVerificationStatus();

	useEffect(() => {
		if (verificationData?.is_email_verified !== undefined) {
			setLocalVerificationStatus(verificationData.is_email_verified);
			localStorage.setItem(
				"is_email_verified",
				String(verificationData.is_email_verified),
			);

			if (verificationData.is_email_verified) {
				toast.success("Email is verified!", {
					description: "You now have full access to all features",
				});
			}
		}
	}, [verificationData]);

	useEffect(() => {
		if (user?.user_email) {
			localStorage.setItem("user_email", user.user_email);
		}
	}, [user?.user_email]);

	const handleRequestVerification = async () => {
		if (!user?.user_email) {
			toast.error("Request failed", {
				description: "User email not available",
			});
			return;
		}

		try {
			await requestVerificationMutation.mutateAsync(user.user_email);
			toast.success("Verification email sent", {
				description: "Please check your inbox for the verification link",
			});
		} catch (error) {
			const errorMessage =
				error instanceof Error
					? error.message
					: "Failed to send verification email";

			toast.error("Request failed", {
				description: errorMessage,
			});
		}
	};

	const handleRefreshStatus = async () => {
		if (!user?.user_email) {
			toast.error("Refresh failed", {
				description: "User email not available",
			});
			return;
		}

		try {
			await refreshStatusMutation.mutateAsync(user.user_email);
		} catch (error) {
			const errorMessage =
				error instanceof Error
					? error.message
					: "Could not refresh verification status.";

			toast.error("Refresh failed", {
				description: errorMessage,
			});
		}
	};

	const userName =
		user?.user_first_name ??
		firstName ??
		localStorage.getItem("first_name") ??
		"Not provided";

	const userEmail = user?.user_email ?? "Not available";

	const isLoading = requestVerificationMutation.isPending;
	const isRefreshing = refreshStatusMutation.isPending || isCheckingStatus;

	const error =
		verificationError?.message ??
		requestVerificationMutation.error?.message ??
		refreshStatusMutation.error?.message;

	return (
		<UserProfilePresenter
			userName={userName}
			userEmail={userEmail}
			isEmailVerified={localVerificationStatus}
			isLoading={isLoading}
			isRefreshing={isRefreshing}
			error={error}
			onRequestVerification={handleRequestVerification}
			onRefreshStatus={handleRefreshStatus}
		/>
	);
}
