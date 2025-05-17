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
import CountrySelector from "@/components/ui/CountrySelector";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../store/auth/AuthContext";
import { type RegisterFormData, registerSchema } from "./RegisterSchema";
import { AUTH_ERRORS, registerUser } from "./UserService";

export default function RegisterForm(_: React.ComponentProps<"div">) {
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
	const { login } = useAuth();
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

	const [showConfirmPassword, setShowConfirmPassword] = useState(false);
	const toggleConfirmPasswordVisibility = useCallback(() => {
		setShowConfirmPassword((prev) => !prev);
	}, []);

	const onSubmit = async (data: RegisterFormData) => {
		try {
			setError("");

			if (isOffline) {
				setError(
					"You are offline. Please connect to the internet to register.",
				);
				return;
			}

			const tokenPair = await registerUser(
				data.email,
				data.password,
				data.first_name,
				data.country_code,
			);
			await login(tokenPair, data.first_name);
			navigate("/");
		} catch (err: unknown) {
			const errorMessage = AUTH_ERRORS.format(err);
			setError(errorMessage);
			console.error("Registration failed:", err);
		}
	};

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Register</CardTitle>
					<CardDescription>Create a new account to get started</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <FormError message={error} className="mb-4" />}

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

							{/* First Name Field */}
							<div className="grid gap-3">
								<Label htmlFor="first_name">First Name</Label>
								<Input
									{...register("first_name")}
									id="first_name"
									type="text"
								/>
								{errors.first_name && (
									<p className="text-sm text-red-500">
										{errors.first_name.message}
									</p>
								)}
							</div>

							{/* Country Code Field */}
							<div className="grid gap-3">
								<CountrySelector
									control={control}
									error={errors.country_code}
								/>
							</div>

							<div className="flex flex-col gap-3">
								<Button
									type="submit"
									disabled={isSubmitting || isOffline}
									className="w-full"
								>
									{isSubmitting
										? "Registering..."
										: isOffline
											? "Offline"
											: "Register"}
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
		</PageLayout>
	);
}
