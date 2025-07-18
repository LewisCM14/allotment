import { Button } from "@/components/ui/Button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { FormError } from "@/components/FormError";
import { PageLayout } from "@/components/layouts/PageLayout";
import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
	allotmentSchema,
	type AllotmentFormData,
} from "../forms/AllotmentSchema";
import {
	createUserAllotment,
	getUserAllotment,
	updateUserAllotment,
	AUTH_ERRORS,
	type IAllotmentResponse,
} from "../services/UserService";

export default function AllotmentPage(_: React.ComponentProps<"div">) {
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
			allotment_width_meters: 0,
			allotment_length_meters: 0,
		},
	});

	// Watch form values for real-time area calculation
	const formValues = useWatch({ control });
	const currentArea =
		(formValues.allotment_width_meters ?? 0) *
		(formValues.allotment_length_meters ?? 0);

	const [existingAllotment, setExistingAllotment] =
		useState<IAllotmentResponse | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string>("");
	const [isOffline, setIsOffline] = useState(!navigator.onLine);
	const { isAuthenticated } = useAuth();
	const navigate = useNavigate();

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
			return;
		}

		const fetchAllotment = async () => {
			try {
				setIsLoading(true);
				setError("");
				const allotmentData = await getUserAllotment();
				setExistingAllotment(allotmentData);

				// Populate form with existing data
				setValue(
					"allotment_postal_zip_code",
					allotmentData.allotment_postal_zip_code,
				);
				setValue(
					"allotment_width_meters",
					allotmentData.allotment_width_meters,
				);
				setValue(
					"allotment_length_meters",
					allotmentData.allotment_length_meters,
				);
			} catch (err) {
				// If allotment doesn't exist, that's fine - form will show placeholders
				console.info("No existing allotment found - user will create one", err);
				setError(""); // Clear any error since this is expected for new users
			} finally {
				setIsLoading(false);
			}
		};

		fetchAllotment();
	}, [isAuthenticated, navigate, setValue]);

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

				let result: IAllotmentResponse;

				if (existingAllotment) {
					// Update existing allotment
					result = await updateUserAllotment(data);
				} else {
					// Create new allotment
					result = await createUserAllotment(data);
				}

				setExistingAllotment(result);
				// Don't change editing state - keep form always editable
			} catch (err: unknown) {
				const errorMessage = AUTH_ERRORS.format(err);
				setError(errorMessage);
				console.error("Allotment operation failed:", err);
			}
		},
		[existingAllotment, isOffline],
	);

	if (isLoading) {
		return (
			<PageLayout variant="default">
				<Card className="w-full">
					<CardContent className="pt-6">
						<div className="text-center">Loading allotment data...</div>
					</CardContent>
				</Card>
			</PageLayout>
		);
	}

	const isUpdate = !!existingAllotment;
	let buttonText = isUpdate ? "Update Allotment" : "Create Allotment";
	if (isSubmitting) {
		buttonText = isUpdate ? "Updating..." : "Creating...";
	} else if (isOffline) {
		buttonText = "Offline";
	}

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Your Allotment</CardTitle>
					<CardDescription>
						{isUpdate
							? "Manage your allotment details"
							: "Create your allotment to get started"}
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <FormError message={error} className="mb-4" />}

						{isOffline && (
							<div className="p-3 mb-4 text-muted-foreground bg-muted/30 rounded border border-muted">
								<p className="text-sm">
									You are currently offline. Connect to the internet to save
									your allotment.
								</p>
							</div>
						)}

						<div className="flex flex-col gap-6">
							<div className="grid gap-3">
								<Label htmlFor="allotment_postal_zip_code">
									Postal/Zip Code
								</Label>
								<Input
									id="allotment_postal_zip_code"
									type="text"
									placeholder="e.g., 12345 or A1A 1A1"
									autoComplete="postal-code"
									{...register("allotment_postal_zip_code")}
									aria-invalid={
										errors.allotment_postal_zip_code ? "true" : "false"
									}
								/>
								{errors.allotment_postal_zip_code && (
									<p className="text-sm text-destructive">
										{errors.allotment_postal_zip_code.message}
									</p>
								)}
							</div>

							<div className="grid gap-3">
								<Label htmlFor="allotment_width_meters">Width (meters)</Label>
								<Input
									id="allotment_width_meters"
									type="number"
									step="0.1"
									min="1"
									max="100"
									placeholder="e.g., 10.5"
									{...register("allotment_width_meters", {
										setValueAs: (value) =>
											value === "" ? 0 : Number.parseFloat(value),
									})}
									aria-invalid={
										errors.allotment_width_meters ? "true" : "false"
									}
								/>
								{errors.allotment_width_meters && (
									<p className="text-sm text-destructive">
										{errors.allotment_width_meters.message}
									</p>
								)}
							</div>

							<div className="grid gap-3">
								<Label htmlFor="allotment_length_meters">Length (meters)</Label>
								<Input
									id="allotment_length_meters"
									type="number"
									step="0.1"
									min="1"
									max="100"
									placeholder="e.g., 20.0"
									{...register("allotment_length_meters", {
										setValueAs: (value) =>
											value === "" ? 0 : Number.parseFloat(value),
									})}
									aria-invalid={
										errors.allotment_length_meters ? "true" : "false"
									}
								/>
								{errors.allotment_length_meters && (
									<p className="text-sm text-destructive">
										{errors.allotment_length_meters.message}
									</p>
								)}
							</div>

							{/* Real-time area display */}
							<div className="p-4 bg-accent/20 border border-accent/30 rounded-lg">
								<div className="flex items-center justify-between">
									<span className="text-sm font-medium text-accent-foreground/80">
										Total Area:
									</span>
									<span className="text-lg font-semibold text-primary">
										{currentArea > 0
											? `${currentArea.toFixed(1)} m²`
											: "0.0 m²"}
									</span>
								</div>
							</div>

							<Button
								type="submit"
								disabled={isSubmitting || isOffline}
								className="w-full"
							>
								<Save className="mr-2 h-4 w-4" />
								{buttonText}
							</Button>
						</div>
					</form>
				</CardContent>
			</Card>
		</PageLayout>
	);
}
