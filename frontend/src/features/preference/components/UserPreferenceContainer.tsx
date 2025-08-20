import { useAuth } from "@/store/auth/AuthContext";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatError } from "@/utils/errorUtils";
import {
	useUserFeedPreferences,
	useFeedTypes,
	useDays,
	useUpdateUserFeedPreference,
} from "../hooks/usePreferences";
import UserPreferencePresenter from "./UserPreferencePresenter";

export default function UserPreferenceContainer() {
	const { isAuthenticated } = useAuth();
	const navigate = useNavigate();
	const [error, setError] = useState<string>("");

	// Data queries
	const {
		data: preferences = [],
		isLoading: preferencesLoading,
		error: preferencesError,
	} = useUserFeedPreferences();

	const {
		data: feedTypes = [],
		isLoading: feedTypesLoading,
		error: feedTypesError,
	} = useFeedTypes();

	const {
		data: days = [],
		isLoading: daysLoading,
		error: daysError,
	} = useDays();

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
		const errors = [preferencesError, feedTypesError, daysError].filter(
			Boolean,
		);
		if (errors.length > 0) {
			const errorMessage = formatError(errors[0]);
			setError(`Failed to load data: ${errorMessage}`);
		} else {
			setError("");
		}
	}, [preferencesError, feedTypesError, daysError]);

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
	const isLoading = preferencesLoading || feedTypesLoading || daysLoading;
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
