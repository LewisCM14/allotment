import { FormError } from "@/components/FormError";
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
import { Loader2, RefreshCw, Edit, Save, X } from "lucide-react";
import { lazy, Suspense, memo } from "react";
import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";
import type { UserProfileFormData } from "../forms/UserProfileSchema";

const CountrySelector = lazy(() => import("@/components/ui/CountrySelector"));

interface UserProfilePresenterProps {
	readonly userName: string;
	readonly userEmail: string;
	readonly userCountryCode: string;
	readonly isEmailVerified: boolean;
	readonly isLoading: boolean;
	readonly isRefreshing: boolean;
	readonly isEditing: boolean;
	readonly isSaving: boolean;
	readonly error?: string;
	readonly register: UseFormRegister<UserProfileFormData>;
	readonly control: Control<UserProfileFormData>;
	readonly errors: FieldErrors<UserProfileFormData>;
	readonly onRequestVerification: () => void;
	readonly onRefreshStatus: () => void;
	readonly onEdit: () => void;
	readonly onSave: () => void;
	readonly onCancel: () => void;
}

const UserProfilePresenter = memo(
	({
		userName,
		userEmail,
		userCountryCode,
		isEmailVerified,
		isLoading,
		isRefreshing,
		isEditing,
		isSaving,
		error,
		register,
		control,
		errors,
		onRequestVerification,
		onRefreshStatus,
		onEdit,
		onSave,
		onCancel,
	}: UserProfilePresenterProps) => {
		return (
			<Card className="w-full">
				<CardHeader>
					<CardTitle className="text-2xl">Profile</CardTitle>
					<CardDescription>Manage your account details</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="space-y-6">
						<div className="grid gap-4">
							<div className="border-b border-border pb-4">
								<div className="flex items-center justify-between mb-2">
									<Label className="font-medium text-muted-foreground">
										Name
									</Label>
									{!isEditing && (
										<Button
											variant="ghost"
											size="sm"
											onClick={onEdit}
											className="h-8 px-2"
										>
											<Edit className="h-4 w-4" />
										</Button>
									)}
								</div>
								{isEditing ? (
									<div className="space-y-2">
										<Input
											{...register("user_first_name")}
											placeholder="Enter your first name"
											className="text-lg"
										/>
										{errors.user_first_name && (
											<p className="text-sm text-destructive">
												{errors.user_first_name.message}
											</p>
										)}
									</div>
								) : (
									<p className="text-lg text-foreground">{userName}</p>
								)}
							</div>

							<div className="border-b border-border pb-4">
								<Label className="font-medium text-muted-foreground mb-2 block">
									Email
								</Label>
								<p className="text-lg text-foreground">{userEmail}</p>
								{isEmailVerified && (
									<p className="text-primary text-sm mt-1">✓ Email verified</p>
								)}
							</div>

							<div className="border-b border-border pb-4">
								{isEditing ? (
									<div className="space-y-2">
										<Suspense
											fallback={
												<div className="h-10 w-full animate-pulse rounded-md bg-card border border-border" />
											}
										>
											<CountrySelector
												control={control}
												name="user_country_code"
												error={errors.user_country_code}
												showLabel={false}
											/>
										</Suspense>
									</div>
								) : (
									<>
										<Label className="font-medium text-muted-foreground mb-2 block">
											Country
										</Label>
										<p className="text-lg text-foreground">{userCountryCode}</p>
									</>
								)}
							</div>
						</div>

						{error && <FormError message={error} className="mb-4" />}

						{!isEmailVerified && (
							<div className="border border-amber-200 p-4 rounded-md bg-amber-50 dark:bg-amber-900/30 mt-6">
								<h3 className="font-medium text-amber-800 dark:text-amber-200">
									Email Not Verified
								</h3>
								<p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
									Please verify your email address to access all features.
								</p>
								<Button
									onClick={onRequestVerification}
									disabled={isLoading}
									variant="outline"
									className="w-full"
								>
									{isLoading ? "Sending..." : "Send Verification Email"}
								</Button>
							</div>
						)}
					</div>
				</CardContent>
				<CardFooter className="flex flex-col sm:flex-row sm:justify-between gap-3 sm:gap-2">
					<Button
						variant="outline"
						size="sm"
						className="flex items-center gap-2 w-full sm:w-auto"
						onClick={onRefreshStatus}
						disabled={isRefreshing}
					>
						{isRefreshing ? (
							<>
								<Loader2 className="h-4 w-4 animate-spin" /> Checking...
							</>
						) : (
							<>
								<RefreshCw className="h-4 w-4" /> Refresh Status
							</>
						)}
					</Button>

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
	},
);

export default UserProfilePresenter;
