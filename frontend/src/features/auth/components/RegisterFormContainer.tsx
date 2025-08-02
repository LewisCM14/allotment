import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { type RegisterFormData, registerSchema } from "../forms/RegisterSchema";
import { registerUser } from "../services/RegistrationService";
import { formatError } from "@/utils/errorUtils";
import { useUserRegistration } from "../hooks/useUserRegistration";
import RegisterFormPresenter from "./RegisterFormPresenter";

export default function RegisterFormContainer() {
	const {
		register,
		handleSubmit,
		control,
		formState: { errors, isSubmitting },
	} = useForm<RegisterFormData>({
		resolver: zodResolver(registerSchema),
		mode: "onBlur",
	});

	const [error, setError] = useState<string>("");
	const [isOffline, setIsOffline] = useState(!navigator.onLine);
	const [showPassword, setShowPassword] = useState(false);
	const [showConfirmPassword, setShowConfirmPassword] = useState(false);

	const { login } = useAuth();
	const navigate = useNavigate();
	const registrationMutation = useUserRegistration();

	// Handle online/offline events
	useEffect(() => {
		const handleOnline = () => setIsOffline(false);
		const handleOffline = () => setIsOffline(true);

		window.addEventListener("online", handleOnline);
		window.addEventListener("offline", handleOffline);

		return () => {
			window.removeEventListener("online", handleOnline);
			window.removeEventListener("offline", handleOffline);
		};
	}, []);

	// Handle password visibility toggles
	const togglePasswordVisibility = useCallback(() => {
		setShowPassword((prev) => !prev);
	}, []);

	const toggleConfirmPasswordVisibility = useCallback(() => {
		setShowConfirmPassword((prev) => !prev);
	}, []);

	const onSubmit = useCallback(
		async (data: RegisterFormData) => {
			try {
				setError("");

				if (isOffline) {
					setError(
						"You are offline. Please connect to the internet to register.",
					);
					return;
				}

				const tokenPair = await registrationMutation.mutateAsync({
					email: data.email,
					password: data.password,
					firstName: data.first_name,
					countryCode: data.country_code,
				});

				await login(tokenPair, data.first_name);
				navigate("/");
			} catch (err: unknown) {
				const errorMessage = formatError(err);
				setError(errorMessage);
			}
		},
		[isOffline, registrationMutation, login, navigate],
	);

	// Derive button text
	let buttonText = "Register";
	if (isSubmitting || registrationMutation.isPending) {
		buttonText = "Registering...";
	} else if (isOffline) {
		buttonText = "Offline";
	}

	return (
		<RegisterFormPresenter
			register={register}
			handleSubmit={handleSubmit}
			control={control}
			errors={errors}
			error={error}
			isOffline={isOffline}
			isSubmitting={isSubmitting}
			isMutating={registrationMutation.isPending}
			showPassword={showPassword}
			showConfirmPassword={showConfirmPassword}
			buttonText={buttonText}
			onSubmit={onSubmit}
			onTogglePasswordVisibility={togglePasswordVisibility}
			onToggleConfirmPasswordVisibility={toggleConfirmPasswordVisibility}
		/>
	);
}
