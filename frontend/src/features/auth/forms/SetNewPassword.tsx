import { FormError } from "@/components/FormError";
import { PageLayout } from "@/components/layouts/PageLayout";
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
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
	type SetNewPasswordFormData,
	setNewPasswordSchema,
} from "./SetNewPasswordSchema";
import { resetPassword } from "../services/AuthService";

export default function SetNewPassword() {
	const [searchParams] = useSearchParams();
	const token = searchParams.get("token");
	const navigate = useNavigate();
	const [isTokenValid, setIsTokenValid] = useState(true);
	const [showPassword, setShowPassword] = useState(false);
	const [showConfirmPassword, setShowConfirmPassword] = useState(false);

	const {
		register,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<SetNewPasswordFormData>({
		resolver: zodResolver(setNewPasswordSchema),
		mode: "onBlur",
	});

	const [error, setError] = useState<string>("");
	const [isOffline, setIsOffline] = useState(!navigator.onLine);

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

	useEffect(() => {
		if (!token) {
			setIsTokenValid(false);
			setError(
				"Invalid or missing reset token. Please request a new password reset.",
			);
		}
	}, [token]);

	const togglePasswordVisibility = useCallback(() => {
		setShowPassword((prev) => !prev);
	}, []);

	const toggleConfirmPasswordVisibility = useCallback(() => {
		setShowConfirmPassword((prev) => !prev);
	}, []);

	const onSubmit = async (data: SetNewPasswordFormData) => {
		try {
			setError("");

			if (isOffline) {
				setError(
					"You are offline. Please connect to the internet to continue.",
				);
				return;
			}

			if (!token) {
				setError(
					"Reset token is missing. Please request a new password reset.",
				);
				return;
			}

			await resetPassword(token, data.password);

			toast.success("Password reset successfully", {
				description: "You can now log in with your new password",
			});

			navigate("/login");
		} catch (error) {
			const errorMessage =
				error instanceof Error
					? error.message
					: "Password reset failed. Please try again.";
			setError(errorMessage);
		}
	};

	if (!isTokenValid) {
		return (
			<PageLayout variant="default">
				<Card className="w-full">
					<CardHeader>
						<CardTitle>Invalid Reset Link</CardTitle>
						<CardDescription>
							This password reset link is invalid or has expired.
						</CardDescription>
					</CardHeader>
					<CardContent>
						<p className="mb-4">Please request a new password reset.</p>
						<Button asChild>
							<Link to="/reset-password">Request New Reset Link</Link>
						</Button>
					</CardContent>
				</Card>
			</PageLayout>
		);
	}

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Set New Password</CardTitle>
					<CardDescription>
						Please enter and confirm your new password
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <FormError message={error} className="mb-4" />}

						{isOffline && (
							<div className="p-3 mb-4 text-amber-800 bg-amber-50 rounded border border-amber-200">
								<p>
									You are currently offline. This feature requires an internet
									connection.
								</p>
							</div>
						)}

						<div className="flex flex-col gap-6">
							{/* Password Field */}
							<div className="grid gap-3">
								<Label htmlFor="password">New Password</Label>
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
										onClick={togglePasswordVisibility}
										aria-label={
											showPassword ? "Hide password" : "Show password"
										}
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
								<Label htmlFor="password_confirm">Confirm New Password</Label>
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
										onClick={toggleConfirmPasswordVisibility}
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

							<Button
								type="submit"
								disabled={isSubmitting || isOffline}
								className="w-full text-white"
							>
								{isSubmitting ? "Setting Password..." : "Set New Password"}
							</Button>
						</div>

						<div className="mt-4 text-center text-sm">
							Remember your password?{" "}
							<Link
								to="/login"
								className="text-primary hover:underline underline-offset-4"
							>
								Back to Login
							</Link>
						</div>
					</form>
				</CardContent>
			</Card>
		</PageLayout>
	);
}
