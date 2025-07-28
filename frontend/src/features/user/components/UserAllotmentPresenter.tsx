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
import { Save } from "lucide-react";
import type {
    FieldErrors,
    UseFormHandleSubmit,
    UseFormRegister,
} from "react-hook-form";
import type { AllotmentFormData } from "../forms/AllotmentSchema";

interface UserAllotmentPresenterProps {
    register: UseFormRegister<AllotmentFormData>;
    handleSubmit: UseFormHandleSubmit<AllotmentFormData>;
    errors: FieldErrors<AllotmentFormData>;
    currentArea: number;
    error: string;
    isOffline: boolean;
    isLoading: boolean;
    isSubmitting: boolean;
    isMutating: boolean;
    isUpdate: boolean;
    buttonText: string;
    onSubmit: (data: AllotmentFormData) => Promise<void>;
}

export default function UserAllotmentPresenter({
    register,
    handleSubmit,
    errors,
    currentArea,
    error,
    isOffline,
    isLoading,
    isSubmitting,
    isMutating,
    isUpdate,
    buttonText,
    onSubmit,
}: UserAllotmentPresenterProps) {
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
                                    placeholder="12345 or A1A 1A1"
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
                                    placeholder="10.5"
                                    {...register("allotment_width_meters", {
                                        setValueAs: (value) =>
                                            value === "" ? undefined : Number.parseFloat(value),
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
                                    placeholder="20.0"
                                    {...register("allotment_length_meters", {
                                        setValueAs: (value) =>
                                            value === "" ? undefined : Number.parseFloat(value),
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
                                disabled={isSubmitting || isMutating || isOffline}
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
