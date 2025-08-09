import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
	allotmentSchema,
	type AllotmentFormData,
} from "../forms/AllotmentSchema";
import { NoAllotmentFoundError } from "../services/AllotmentService";
import { formatError } from "@/utils/errorUtils";
import {
	useUserAllotment,
	useCreateUserAllotment,
	useUpdateUserAllotment,
} from "../hooks/useUserAllotment";
import UserAllotmentPresenter from "./UserAllotmentPresenter";

export default function UserAllotmentContainer() {
	const {
		register,
		handleSubmit,
		setValue,
		control,
		reset,
		formState: { errors },
	} = useForm<AllotmentFormData>({
		resolver: zodResolver(allotmentSchema),
		mode: "onBlur",
		defaultValues: {
			allotment_postal_zip_code: "",
			allotment_width_meters: undefined,
			allotment_length_meters: undefined,
		},
	});

	const {
		data: existingAllotment,
		isLoading,
		error: queryError,
	} = useUserAllotment();

	const createAllotmentMutation = useCreateUserAllotment();
	const updateAllotmentMutation = useUpdateUserAllotment();

	// Watch form values for real-time area calculation
	const formValues = useWatch({ control });
	const currentArea =
		(formValues.allotment_width_meters ?? 0) *
		(formValues.allotment_length_meters ?? 0);

	const [error, setError] = useState<string>("");
	const [isEditing, setIsEditing] = useState(false);
	const { isAuthenticated } = useAuth();
	const navigate = useNavigate();

	// Handle authentication redirect
	useEffect(() => {
		if (!isAuthenticated) {
			navigate("/login");
		}
	}, [isAuthenticated, navigate]);

	// Update form when allotment data is loaded
	useEffect(() => {
		if (existingAllotment) {
			setValue(
				"allotment_postal_zip_code",
				existingAllotment.allotment_postal_zip_code,
			);
			setValue(
				"allotment_width_meters",
				existingAllotment.allotment_width_meters,
			);
			setValue(
				"allotment_length_meters",
				existingAllotment.allotment_length_meters,
			);
		}
	}, [existingAllotment, setValue]);

	// Handle errors
	useEffect(() => {
		if (queryError) {
			if (queryError instanceof NoAllotmentFoundError) {
				setError(""); // Clear any error since this is expected for new users
				setIsEditing(true); // Start in edit mode for new users
			} else {
				const errorMessage = formatError(queryError);
				setError(`Failed to load allotment data: ${errorMessage}`);
			}
		} else {
			setError("");
		}
	}, [queryError]);

	const handleEdit = useCallback(() => {
		setIsEditing(true);
		setError("");
	}, []);

	const handleCancel = useCallback(() => {
		setIsEditing(false);
		setError("");
		// Reset form to original values
		if (existingAllotment) {
			setValue(
				"allotment_postal_zip_code",
				existingAllotment.allotment_postal_zip_code,
			);
			setValue(
				"allotment_width_meters",
				existingAllotment.allotment_width_meters,
			);
			setValue(
				"allotment_length_meters",
				existingAllotment.allotment_length_meters,
			);
		} else {
			reset();
		}
	}, [existingAllotment, setValue, reset]);

	const handleSave = useCallback(
		handleSubmit(async (data: AllotmentFormData) => {
			try {
				setError("");

				if (existingAllotment) {
					// Update existing allotment
					await updateAllotmentMutation.mutateAsync(data);
				} else {
					// Create new allotment
					await createAllotmentMutation.mutateAsync(data);
				}
				setIsEditing(false);
			} catch (err: unknown) {
				const errorMessage = formatError(err);
				setError(errorMessage);
			}
		}),
		[],
	);

	// Derive presentation data
	const postalCode = existingAllotment?.allotment_postal_zip_code ?? "";
	const width = existingAllotment?.allotment_width_meters ?? 0;
	const length = existingAllotment?.allotment_length_meters ?? 0;

	const isSaving =
		createAllotmentMutation.isPending || updateAllotmentMutation.isPending;

	const currentError =
		error ??
		createAllotmentMutation.error?.message ??
		updateAllotmentMutation.error?.message;

	return (
		<UserAllotmentPresenter
			postalCode={postalCode}
			width={width}
			length={length}
			currentArea={currentArea}
			isEditing={isEditing}
			isLoading={isLoading}
			isSaving={isSaving}
			error={currentError}
			register={register}
			errors={errors}
			onEdit={handleEdit}
			onSave={handleSave}
			onCancel={handleCancel}
			hasExistingData={!!existingAllotment}
		/>
	);
}
