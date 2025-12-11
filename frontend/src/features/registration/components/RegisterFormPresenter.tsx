import { FormError } from "@/components/FormError";
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
import { Eye, EyeOff } from "lucide-react";
import { Suspense, lazy } from "react";
import type {
	Control,
	FieldErrors,
	UseFormHandleSubmit,
	UseFormRegister,
} from "react-hook-form";
import { Link } from "react-router-dom";
import type { RegisterFormData } from "../forms/RegisterSchema";

const CountrySelector = lazy(() => import("@/components/ui/CountrySelector"));

interface RegisterFormPresenterProps {
	readonly register: UseFormRegister<RegisterFormData>;
	readonly handleSubmit: UseFormHandleSubmit<RegisterFormData>;
	readonly control: Control<RegisterFormData>;
	readonly errors: FieldErrors<RegisterFormData>;
	readonly error: string;
	readonly isOffline: boolean;
	readonly isSubmitting: boolean;
	readonly isMutating: boolean;
	readonly showPassword: boolean;
	readonly showConfirmPassword: boolean;
	readonly buttonText: string;
	readonly onSubmit: (data: RegisterFormData) => Promise<void>;
	readonly onTogglePasswordVisibility: () => void;
	readonly onToggleConfirmPasswordVisibility: () => void;
}

export default function RegisterFormPresenter({
	register,
	handleSubmit,
	control,
	errors,
	error,
	isOffline,
	isSubmitting,
	isMutating,
	showPassword,
	showConfirmPassword,
	buttonText,
	onSubmit,
	onTogglePasswordVisibility,
	onToggleConfirmPasswordVisibility,
}: RegisterFormPresenterProps) {
	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle>Register</CardTitle>
				<CardDescription>Create a new account to get started</CardDescription>
			</CardHeader>
			<CardContent>
				<form onSubmit={handleSubmit(onSubmit)}>
					<div aria-live="polite" aria-atomic="true">
						{error && <FormError message={error} className="mb-4" />}
					</div>

					{isOffline && (
						<div className="p-3 mb-4 text-amber-800 bg-amber-50 rounded border border-amber-200">
							<p>
								You are currently offline. Registration requires an internet
								connection.
							</p>
						</div>
					)}

					<div className="flex flex-col gap-6">
						{/* Email Field */}
						<div className="grid gap-3">
							<Label htmlFor="email">Email</Label>
							<Input
								{...register("email")}
								id="email"
								type="email"
								placeholder="m@example.com"
								autoComplete="email"
							/>
							{errors.email && (
								<p className="text-sm text-red-500">{errors.email.message}</p>
							)}
						</div>

						{/* Password Field */}
						<div className="grid gap-3">
							<Label htmlFor="password">Password</Label>
							<div className="relative">
								<Input
									{...register("password")}
									id="password"
									type={showPassword ? "text" : "password"}
									autoComplete="new-password"
								/>
								<Button
									type="button"
									variant="ghost"
									size="icon"
									className="absolute right-0 top-0 h-full px-3"
									onClick={onTogglePasswordVisibility}
									aria-label={showPassword ? "Hide password" : "Show password"}
								>
									{showPassword ? (
										<EyeOff className="h-4 w-4" />
									) : (
										<Eye className="h-4 w-4" />
									)}
								</Button>
							</div>
							{errors.password && (
								<p className="text-sm text-red-500">
									{errors.password.message}
								</p>
							)}
						</div>

						{/* Confirm Password Field */}
						<div className="grid gap-3">
							<Label htmlFor="password_confirm">Confirm Password</Label>
							<div className="relative">
								<Input
									{...register("password_confirm")}
									id="password_confirm"
									type={showConfirmPassword ? "text" : "password"}
									autoComplete="new-password"
								/>
								<Button
									type="button"
									variant="ghost"
									size="icon"
									className="absolute right-0 top-0 h-full px-3"
									onClick={onToggleConfirmPasswordVisibility}
									aria-label={
										showConfirmPassword ? "Hide password" : "Show password"
									}
								>
									{showConfirmPassword ? (
										<EyeOff className="h-4 w-4" />
									) : (
										<Eye className="h-4 w-4" />
									)}
								</Button>
							</div>
							{errors.password_confirm && (
								<p className="text-sm text-red-500">
									{errors.password_confirm.message}
								</p>
							)}
						</div>

						{/* First Name Field */}
						<div className="grid gap-3">
							<Label htmlFor="first_name">First Name</Label>
							<Input
								{...register("first_name")}
								id="first_name"
								type="text"
								autoComplete="given-name"
							/>
							{errors.first_name && (
								<p className="text-sm text-red-500">
									{errors.first_name.message}
								</p>
							)}
						</div>

						{/* Country Code Field */}
						<div className="grid gap-3">
							<Suspense
								fallback={
									<div className="h-10 w-full animate-pulse rounded-md bg-card border border-border" />
								}
							>
								<CountrySelector
									control={control}
									name="country_code"
									error={errors.country_code}
								/>
							</Suspense>
						</div>

						<div className="flex flex-col gap-3">
							<Button
								type="submit"
								disabled={isSubmitting || isMutating || isOffline}
								aria-disabled={isSubmitting || isMutating || isOffline}
								className="w-full text-white"
							>
								{buttonText}
							</Button>
						</div>
					</div>
					<div className="mt-4 text-center text-sm">
						Already have an account?{" "}
						<Link to="/login" className="underline underline-offset-4">
							Login
						</Link>
					</div>
				</form>
			</CardContent>
		</Card>
	);
}
