import { Button } from "@/components/ui/Button";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { FormError } from "@/components/FormError";
import { Save, Loader2, Edit, X } from "lucide-react";
import type { FieldErrors, UseFormRegister } from "react-hook-form";
import type { AllotmentFormData } from "../forms/AllotmentSchema";

interface UserAllotmentPresenterProps {
	readonly postalCode: string;
	readonly width: number;
	readonly length: number;
	readonly currentArea: number;
	readonly isEditing: boolean;
	readonly isLoading: boolean;
	readonly isSaving: boolean;
	readonly error?: string;
	readonly register: UseFormRegister<AllotmentFormData>;
	readonly errors: FieldErrors<AllotmentFormData>;
	readonly onEdit: () => void;
	readonly onSave: () => void;
	readonly onCancel: () => void;
	readonly hasExistingData: boolean;
}

export default function UserAllotmentPresenter({
	postalCode,
	width,
	length,
	currentArea,
	isEditing,
	isLoading,
	isSaving,
	error,
	register,
	errors,
	onEdit,
	onSave,
	onCancel,
	hasExistingData,
}: UserAllotmentPresenterProps) {
	if (isLoading) {
		return (
			<div className="flex justify-center items-center h-64">
				<Loader2 className="h-8 w-8 animate-spin text-primary" />
				<p className="ml-2">Loading allotment data...</p>
			</div>
		);
	}

	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle className="text-2xl">Your Allotment</CardTitle>
				<CardDescription>
					{hasExistingData
						? "Manage your allotment details"
						: "Add your allotment details to get started"}
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="space-y-6">
					<div className="grid gap-4">
						<div className="border-b border-border pb-4">
							<div className="flex items-center justify-between mb-2">
								<Label
									htmlFor="allotment_postal_zip_code"
									className="font-medium text-muted-foreground"
								>
									Postal/Zip Code
								</Label>
								{!isEditing && (
									<Button
										variant="ghost"
										size="sm"
										onClick={onEdit}
										className="h-8 px-2"
										aria-label="Edit allotment details"
									>
										<Edit className="h-4 w-4" />
									</Button>
								)}
							</div>
							{isEditing ? (
								<div className="space-y-2">
									<Input
										{...register("allotment_postal_zip_code")}
										id="allotment_postal_zip_code"
										placeholder="12345 or A1A 1A1"
										autoComplete="postal-code"
										className="text-lg"
									/>
									{errors.allotment_postal_zip_code && (
										<p className="text-sm text-destructive">
											{errors.allotment_postal_zip_code.message}
										</p>
									)}
								</div>
							) : (
								<p
									className={`text-lg ${!hasExistingData ? "text-muted-foreground italic" : "text-foreground"}`}
								>
									{postalCode ||
										(hasExistingData
											? "Not provided"
											: "Enter your postal/zip code")}
								</p>
							)}
						</div>

						<div className="border-b border-border pb-4">
							<Label
								htmlFor="allotment_width_meters"
								className="font-medium text-muted-foreground mb-2 block"
							>
								Width (meters)
							</Label>
							{isEditing ? (
								<div className="space-y-2">
									<Input
										{...register("allotment_width_meters", {
											setValueAs: (value) =>
												value === "" ? undefined : Number.parseFloat(value),
										})}
										id="allotment_width_meters"
										type="number"
										step="0.1"
										min="1"
										max="100"
										placeholder="10.5"
										className="text-lg"
									/>
									{errors.allotment_width_meters && (
										<p className="text-sm text-destructive">
											{errors.allotment_width_meters.message}
										</p>
									)}
								</div>
							) : (
								<p
									className={`text-lg ${!hasExistingData ? "text-muted-foreground italic" : "text-foreground"}`}
								>
									{width
										? `${width} m`
										: hasExistingData
											? "Not provided"
											: "Enter width in meters"}
								</p>
							)}
						</div>

						<div className="border-b border-border pb-4">
							<Label
								htmlFor="allotment_length_meters"
								className="font-medium text-muted-foreground mb-2 block"
							>
								Length (meters)
							</Label>
							{isEditing ? (
								<div className="space-y-2">
									<Input
										{...register("allotment_length_meters", {
											setValueAs: (value) =>
												value === "" ? undefined : Number.parseFloat(value),
										})}
										id="allotment_length_meters"
										type="number"
										step="0.1"
										min="1"
										max="100"
										placeholder="20.0"
										className="text-lg"
									/>
									{errors.allotment_length_meters && (
										<p className="text-sm text-destructive">
											{errors.allotment_length_meters.message}
										</p>
									)}
								</div>
							) : (
								<p
									className={`text-lg ${!hasExistingData ? "text-muted-foreground italic" : "text-foreground"}`}
								>
									{length
										? `${length} m`
										: hasExistingData
											? "Not provided"
											: "Enter length in meters"}
								</p>
							)}
						</div>

						<div className="border-b border-border pb-4">
							<Label className="font-medium text-muted-foreground mb-2 block">
								Total Area
							</Label>
							<p
								className={`text-lg font-semibold ${!hasExistingData && currentArea === 0 ? "text-muted-foreground italic" : "text-primary"}`}
							>
								{currentArea > 0
									? `${currentArea.toFixed(1)} m²`
									: hasExistingData
										? "0.0 m²"
										: "Will calculate automatically"}
							</p>
						</div>
					</div>

					{error && <FormError message={error} className="mb-4" />}
				</div>
			</CardContent>
			<CardFooter className="flex justify-between">
				<div />
				{isEditing && (
					<div className="flex items-center gap-2">
						<Button
							variant="outline"
							size="sm"
							onClick={onCancel}
							disabled={isSaving}
						>
							<X className="h-4 w-4 mr-1" />
							Cancel
						</Button>
						<Button size="sm" onClick={onSave} disabled={isSaving}>
							{isSaving ? (
								<>
									<Loader2 className="h-4 w-4 animate-spin mr-1" />
									Saving...
								</>
							) : (
								<>
									<Save className="h-4 w-4 mr-1" />
									Save
								</>
							)}
						</Button>
					</div>
				)}
			</CardFooter>
		</Card>
	);
}
