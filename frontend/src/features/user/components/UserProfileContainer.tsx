import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
	userProfileSchema,
	type UserProfileFormData,
} from "../forms/UserProfileSchema";
import { formatError } from "@/utils/errorUtils";
import { errorMonitor } from "@/services/errorMonitoring";
import {
	useUserProfile,
	useUpdateUserProfile,
	useEmailVerificationStatus,
	useRequestEmailVerification,
	useRefreshVerificationStatus,
} from "../hooks/useUserProfile";
import UserProfilePresenter from "./UserProfilePresenter";

export default function UserProfileContainer() {
	const { user, firstName, isAuthenticated } = useAuth();
	const navigate = useNavigate();

	const {
		register,
		handleSubmit,
		setValue,
		control,
		reset,
		formState: { errors },
	} = useForm<UserProfileFormData>({
		resolver: zodResolver(userProfileSchema),
		mode: "onBlur",
		defaultValues: {
			user_first_name: "",
			user_country_code: "",
		},
	});

	const {
		data: profileData,
		isLoading: isProfileLoading,
		error: profileError,
	} = useUserProfile();

	const {
		data: verificationData,
		isLoading: isCheckingStatus,
		error: verificationError,
	} = useEmailVerificationStatus(user?.user_email || profileData?.user_email);

	const updateProfileMutation = useUpdateUserProfile();
	const requestVerificationMutation = useRequestEmailVerification();
	const refreshStatusMutation = useRefreshVerificationStatus();

	const [error, setError] = useState<string>("");
	const [isEditing, setIsEditing] = useState(false);
	const [isOffline, setIsOffline] = useState(!navigator.onLine);
	const [localVerificationStatus, setLocalVerificationStatus] = useState(
		user?.isEmailVerified ??
			localStorage.getItem("is_email_verified") === "true",
	);

	// Handle online/offline events
	useEffect(() => {
		const handleOnline = () => setIsOffline(false);
		const handleOffline = () => setIsOffline(true);

		if (typeof window !== "undefined" && window.addEventListener) {
			window.addEventListener("online", handleOnline);
			window.addEventListener("offline", handleOffline);

			return () => {
				if (window.removeEventListener) {
					window.removeEventListener("online", handleOnline);
					window.removeEventListener("offline", handleOffline);
				}
			};
		}
	}, []);

	useEffect(() => {
		if (!isAuthenticated) {
			navigate("/login");
		}
	}, [isAuthenticated, navigate]);

	// Update form when profile data is loaded
	useEffect(() => {
		if (profileData) {
			setValue("user_first_name", profileData.user_first_name);
			setValue("user_country_code", profileData.user_country_code);
		}
	}, [profileData, setValue]);

	// Update verification status
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

	// Handle errors
	useEffect(() => {
		if (profileError) {
			const errorMessage = formatError(profileError);
			setError(`Failed to load profile data: ${errorMessage}`);
			errorMonitor.captureException(profileError, {
				context: "userProfile.loadData",
				url: window.location.href,
			});
		} else {
			setError("");
		}
	}, [profileError]);

	// Store user email
	useEffect(() => {
		const email = user?.user_email || profileData?.user_email;
		if (email) {
			localStorage.setItem("user_email", email);
		}
	}, [user?.user_email, profileData?.user_email]);

	const handleEdit = useCallback(() => {
		setIsEditing(true);
		setError("");
	}, []);

	const handleCancel = useCallback(() => {
		setIsEditing(false);
		setError("");
		// Reset form to original values
		if (profileData) {
			reset({
				user_first_name: profileData.user_first_name,
				user_country_code: profileData.user_country_code,
			});
		}
	}, [profileData, reset]);

	const handleSave = useCallback(
		handleSubmit(async (data: UserProfileFormData) => {
			try {
				setError("");

				if (isOffline) {
					const offlineError =
						"You are offline. Please connect to the internet to save your profile.";
					setError(offlineError);
					errorMonitor.captureMessage(offlineError, {
						context: "userProfile.save.offline",
						data: data,
					});
					return;
				}

				await updateProfileMutation.mutateAsync(data);
				setIsEditing(false);
				toast.success("Profile updated successfully!");
			} catch (err: unknown) {
				const errorMessage = formatError(err);
				setError(errorMessage);
				errorMonitor.captureException(err, {
					context: "userProfile.save",
					data: data,
					url: window.location.href,
				});
				toast.error("Update failed", {
					description: errorMessage,
				});
			}
		}),
		[],
	);

	const handleRequestVerification = useCallback(async () => {
		const email = user?.user_email || profileData?.user_email;
		if (!email) {
			const noEmailError = "Email address not available";
			setError(noEmailError);
			errorMonitor.captureMessage(noEmailError, {
				context: "userProfile.requestVerification.noEmail",
			});
			toast.error("Request failed", {
				description: "User email not available",
			});
			return;
		}

		try {
			setError("");
			await requestVerificationMutation.mutateAsync(email);
			toast.success("Verification email sent", {
				description: "Please check your inbox for the verification link",
			});
		} catch (err: unknown) {
			const errorMessage = formatError(err);
			setError(errorMessage);
			errorMonitor.captureException(err, {
				context: "userProfile.requestVerification",
				email: email,
				url: window.location.href,
			});
			toast.error("Request failed", {
				description: errorMessage,
			});
		}
	}, [user?.user_email, profileData?.user_email, requestVerificationMutation]);

	const handleRefreshStatus = useCallback(async () => {
		const email = user?.user_email || profileData?.user_email;
		if (!email) {
			const noEmailError = "Email address not available";
			setError(noEmailError);
			errorMonitor.captureMessage(noEmailError, {
				context: "userProfile.refreshStatus.noEmail",
			});
			toast.error("Refresh failed", {
				description: "User email not available",
			});
			return;
		}

		try {
			setError("");
			await refreshStatusMutation.mutateAsync(email);
		} catch (err: unknown) {
			const errorMessage = formatError(err);
			setError(errorMessage);
			errorMonitor.captureException(err, {
				context: "userProfile.refreshStatus",
				email: email,
				url: window.location.href,
			});
			toast.error("Refresh failed", {
				description: errorMessage,
			});
		}
	}, [user?.user_email, profileData?.user_email, refreshStatusMutation]);

	// Derive presentation data
	const userName =
		profileData?.user_first_name ??
		user?.user_first_name ??
		firstName ??
		localStorage.getItem("first_name") ??
		"Not provided";

	const userEmail =
		profileData?.user_email ?? user?.user_email ?? "Not available";

	const userCountryCode = profileData?.user_country_code ?? "Not provided";

	const isLoading = requestVerificationMutation.isPending;
	const isRefreshing = refreshStatusMutation.isPending || isCheckingStatus;
	const isSaving = updateProfileMutation.isPending;

	const currentError =
		error ||
		verificationError?.message ||
		requestVerificationMutation.error?.message ||
		refreshStatusMutation.error?.message ||
		updateProfileMutation.error?.message;

	return (
		<UserProfilePresenter
			userName={userName}
			userEmail={userEmail}
			userCountryCode={userCountryCode}
			isEmailVerified={localVerificationStatus}
			isLoading={isLoading}
			isRefreshing={isRefreshing}
			isEditing={isEditing}
			isSaving={isSaving}
			error={currentError}
			register={register}
			control={control}
			errors={errors}
			onRequestVerification={handleRequestVerification}
			onRefreshStatus={handleRefreshStatus}
			onEdit={handleEdit}
			onSave={handleSave}
			onCancel={handleCancel}
		/>
	);
}
