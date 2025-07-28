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
import { errorMonitor } from "@/services/errorMonitoring";
import { useAuth } from "@/store/auth/AuthContext";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import type { LoginFormData } from "./LoginSchema";
import { loginSchema } from "./LoginSchema";
import { loginUser } from "../services/UserService";

function LoginForm() {
	const {
		register,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<LoginFormData>({
		resolver: zodResolver(loginSchema),
		mode: "onBlur",
	});
	const { login } = useAuth();
	const [error, setError] = useState<string>("");
	const navigate = useNavigate();
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

	const [showPassword, setShowPassword] = useState(false);
	const togglePasswordVisibility = useCallback(() => {
		setShowPassword((prev) => !prev);
	}, []);

	const onSubmit = async (data: LoginFormData) => {
		try {
			setError("");

			if (isOffline) {
				setError("You are offline. Please connect to the internet to login.");
				return;
			}

			const result = await loginUser(data.email, data.password);

			const userData = {
				user_id: result.userData.user_id || "",
				user_email: result.userData.user_email,
				is_email_verified: result.userData.is_email_verified || false,
			};

			await login(result.tokens, result.firstName, userData);
			navigate("/");
		} catch (err: unknown) {
			if (err instanceof Error) {
				setError(err.message);
			} else {
				setError("An unexpected error occurred. Please try again.");
				errorMonitor.captureMessage("Login caught a non-Error throwable", {
					errorDetails: String(err),
				});
			}
		}
	};

	const getButtonText = () => {
		if (isSubmitting) {
			return "Logging in...";
		}
		if (isOffline) {
			return "Offline";
		}
		return "Login";
	};

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Login</CardTitle>
					<CardDescription>
						Enter your email below to login to your account
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <FormError message={error} className="mb-4" />}

						{isOffline && (
							<div className="p-3 mb-4 text-amber-800 bg-amber-50 rounded border border-amber-200">
								<p>
									You are currently offline. Login requires an internet
									connection.
								</p>
							</div>
						)}

						<div className="flex flex-col gap-6">
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
							<div className="grid gap-3">
								<div className="flex items-center">
									<Label htmlFor="password">Password</Label>
								</div>
								<div className="relative">
									<Input
										{...register("password")}
										id="password"
										type={showPassword ? "text" : "password"}
										autoComplete="current-password"
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
								<div className="text-sm text-right">
									<Link
										to="/reset-password"
										className="text-sm text-primary hover:underline underline-offset-4"
									>
										Forgot your password?
									</Link>
								</div>
							</div>
							<div className="flex flex-col gap-3">
								<Button
									type="submit"
									disabled={isSubmitting || isOffline}
									className="w-full"
								>
									{getButtonText()}
								</Button>
							</div>
						</div>
						<div className="mt-4 text-center text-sm">
							Don&apos;t have an account?{" "}
							<Link to="/register" className="underline underline-offset-4">
								Register
							</Link>
						</div>
					</form>
				</CardContent>
			</Card>
		</PageLayout>
	);
}

export default LoginForm;
