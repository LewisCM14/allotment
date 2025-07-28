import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
    allotmentSchema,
    type AllotmentFormData,
} from "../forms/AllotmentSchema";
import { AUTH_ERRORS, NoAllotmentFoundError } from "../services/UserService";
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
        formState: { errors, isSubmitting },
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
    const [isOffline, setIsOffline] = useState(!navigator.onLine);
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

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

    useEffect(() => {
        if (queryError) {
            if (queryError instanceof NoAllotmentFoundError) {
                setError(""); // Clear any error since this is expected for new users
            } else {
                const errorMessage = AUTH_ERRORS.format(queryError);
                setError(`Failed to load allotment data: ${errorMessage}`);
            }
        } else {
            setError("");
        }
    }, [queryError]);

    // Handle form submission
    const onSubmit = useCallback(
        async (data: AllotmentFormData) => {
            try {
                setError("");

                if (isOffline) {
                    setError(
                        "You are offline. Please connect to the internet to save your allotment.",
                    );
                    return;
                }

                if (existingAllotment) {
                    // Update existing allotment
                    await updateAllotmentMutation.mutateAsync(data);
                } else {
                    // Create new allotment
                    await createAllotmentMutation.mutateAsync(data);
                }
            } catch (err: unknown) {
                const errorMessage = AUTH_ERRORS.format(err);
                setError(errorMessage);
            }
        },
        [
            existingAllotment,
            isOffline,
            createAllotmentMutation,
            updateAllotmentMutation,
        ],
    );

    // Derive presentation data
    const isUpdate = !!existingAllotment;
    const isMutating =
        createAllotmentMutation.isPending || updateAllotmentMutation.isPending;

    let buttonText = isUpdate ? "Update Allotment" : "Create Allotment";
    if (isSubmitting || isMutating) {
        buttonText = isUpdate ? "Updating..." : "Creating...";
    } else if (isOffline) {
        buttonText = "Offline";
    }

    return (
        <UserAllotmentPresenter
            register={register}
            handleSubmit={handleSubmit}
            errors={errors}
            currentArea={currentArea}
            error={error}
            isOffline={isOffline}
            isLoading={isLoading}
            isSubmitting={isSubmitting}
            isMutating={isMutating}
            isUpdate={isUpdate}
            buttonText={buttonText}
            onSubmit={onSubmit}
        />
    );
}
