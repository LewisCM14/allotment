import { memo } from "react";
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
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
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

// Helper functions to reduce cognitive complexity
function getDisplayText(
	value: string | number,
	hasData: boolean,
	placeholder: string,
	unit?: string,
): string {
	if (value) {
		return unit ? `${value} ${unit}` : String(value);
	}
	return hasData ? "Not provided" : placeholder;
}

function getDisplayClassName(hasData: boolean): string {
	return `text-lg ${!hasData ? "text-muted-foreground italic" : "text-foreground"}`;
}

function getAreaDisplayText(area: number, hasData: boolean): string {
	if (area > 0) {
		return `${area.toFixed(1)} m²`;
	}
	return hasData ? "0.0 m²" : "Will calculate automatically";
}

function getAreaClassName(hasData: boolean, area: number): string {
	const baseClass = "text-lg font-semibold";
	const colorClass =
		!hasData && area === 0 ? "text-muted-foreground italic" : "text-primary";
	return `${baseClass} ${colorClass}`;
}

const PostalCodeField = memo(function PostalCodeField({
	isEditing,
	register,
	errors,
	postalCode,
	hasExistingData,
	onEdit,
}: {
	readonly isEditing: boolean;
	readonly register: UseFormRegister<AllotmentFormData>;
	readonly errors: FieldErrors<AllotmentFormData>;
	readonly postalCode: string;
	readonly hasExistingData: boolean;
	readonly onEdit: () => void;
}) {
	return (
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
				<p className={getDisplayClassName(hasExistingData)}>
					{getDisplayText(
						postalCode,
						hasExistingData,
						"Enter your postal/zip code",
					)}
				</p>
			)}
		</div>
	);
});

const DimensionField = memo(function DimensionField({
	fieldName,
	label,
	placeholder,
	isEditing,
	register,
	errors,
	value,
	hasExistingData,
}: {
	readonly fieldName: "allotment_width_meters" | "allotment_length_meters";
	readonly label: string;
	readonly placeholder: string;
	readonly isEditing: boolean;
	readonly register: UseFormRegister<AllotmentFormData>;
	readonly errors: FieldErrors<AllotmentFormData>;
	readonly value: number;
	readonly hasExistingData: boolean;
}) {
	const placeholderText = `Enter ${label.toLowerCase()}`;

	return (
		<div className="border-b border-border pb-4">
			<Label
				htmlFor={fieldName}
				className="font-medium text-muted-foreground mb-2 block"
			>
				{label}
			</Label>
			{isEditing ? (
				<div className="space-y-2">
					<Input
						{...register(fieldName, {
							setValueAs: (value) =>
								value === "" ? undefined : Number.parseFloat(value),
						})}
						id={fieldName}
						type="number"
						step="0.1"
						min="1"
						max="100"
						placeholder={placeholder}
						className="text-lg"
					/>
					{errors[fieldName] && (
						<p className="text-sm text-destructive">
							{errors[fieldName]?.message}
						</p>
					)}
				</div>
			) : (
				<p className={getDisplayClassName(hasExistingData)}>
					{getDisplayText(value, hasExistingData, placeholderText, "m")}
				</p>
			)}
		</div>
	);
});

function UserAllotmentPresenter({
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
			<LoadingSpinner
				size="lg"
				className="h-64"
				aria-label="Loading allotment data"
			/>
		);
	}

	const cardDescription = hasExistingData
		? "Manage your allotment details"
		: "Add your allotment details to get started";

	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle className="text-2xl">Your Allotment</CardTitle>
				<CardDescription>{cardDescription}</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="space-y-6">
					<div className="grid gap-4">
						<PostalCodeField
							isEditing={isEditing}
							register={register}
							errors={errors}
							postalCode={postalCode}
							hasExistingData={hasExistingData}
							onEdit={onEdit}
						/>

						<DimensionField
							fieldName="allotment_width_meters"
							label="Width (meters)"
							placeholder="10.5"
							isEditing={isEditing}
							register={register}
							errors={errors}
							value={width}
							hasExistingData={hasExistingData}
						/>

						<DimensionField
							fieldName="allotment_length_meters"
							label="Length (meters)"
							placeholder="20.0"
							isEditing={isEditing}
							register={register}
							errors={errors}
							value={length}
							hasExistingData={hasExistingData}
						/>

						<div className="border-b border-border pb-4">
							<Label className="font-medium text-muted-foreground mb-2 block">
								Total Area
							</Label>
							<p className={getAreaClassName(hasExistingData, currentArea)}>
								{getAreaDisplayText(currentArea, hasExistingData)}
							</p>
						</div>
					</div>

					{error && <FormError message={error} className="mb-4" />}
				</div>
			</CardContent>
			<CardFooter className="flex flex-col sm:flex-row sm:justify-between gap-3 sm:gap-2">
				<div className="hidden sm:block" />
				{isEditing && (
					<div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
						<Button
							variant="outline"
							size="sm"
							className="w-full sm:w-auto"
							onClick={onCancel}
							disabled={isSaving}
						>
							<X className="h-4 w-4 mr-1" />
							Cancel
						</Button>
						<Button
							size="sm"
							className="w-full sm:w-auto text-white"
							onClick={onSave}
							disabled={isSaving}
						>
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

export default memo(UserAllotmentPresenter);
