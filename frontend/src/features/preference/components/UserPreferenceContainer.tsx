import { useAuth } from "@/store/auth/AuthContext";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatError } from "@/utils/errorUtils";
import {
	useUserPreferencesAggregate,
	useUpdateUserFeedPreference,
} from "../hooks/usePreferences";
import UserPreferencePresenter from "./UserPreferencePresenter";

export default function UserPreferenceContainer() {
	const { isAuthenticated } = useAuth();
	const navigate = useNavigate();
	const [error, setError] = useState<string>("");

	// Data query (aggregate)
	const {
		data: preferencesAggregate,
		isLoading: preferencesLoading,
		error: preferencesError,
	} = useUserPreferencesAggregate();

	const preferences = preferencesAggregate?.user_feed_days ?? [];
	const feedTypes = preferencesAggregate?.available_feeds ?? [];
	const days = preferencesAggregate?.available_days ?? [];

	// Mutation
	const updatePreferenceMutation = useUpdateUserFeedPreference();

	// Handle authentication redirect
	useEffect(() => {
		if (!isAuthenticated) {
			navigate("/login");
		}
	}, [isAuthenticated, navigate]);

	// Handle errors
	useEffect(() => {
		if (preferencesError) {
			const errorMessage = formatError(preferencesError);
			setError(`Failed to load data: ${errorMessage}`);
		} else {
			setError("");
		}
	}, [preferencesError]);

	const handleUpdatePreference = useCallback(
		async (feedId: string, dayId: string) => {
			try {
				setError("");
				// Always update the preference (PUT)
				await updatePreferenceMutation.mutateAsync({
					feedId,
					data: { day_id: dayId },
				});
			} catch (err: unknown) {
				const errorMessage = formatError(err);
				setError(errorMessage);
			}
		},
		[updatePreferenceMutation],
	);

	// Calculate loading and saving states
	const isLoading = preferencesLoading;
	const isSaving = updatePreferenceMutation.isPending;

	// Derive current error
	const currentError = error || updatePreferenceMutation.error?.message;

	return (
		<UserPreferencePresenter
			feedTypes={feedTypes}
			days={days}
			preferences={preferences}
			isLoading={isLoading}
			isSaving={isSaving}
			error={currentError}
			onUpdatePreference={handleUpdatePreference}
		/>
	);
}
