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

import {
	Command,
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
} from "@/components/ui/Command";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/Popover";
import { getCountryOptions } from "@/lib/countries";
import { zodResolver } from "@hookform/resolvers/zod";
import { Check, ChevronsUpDown, Eye, EyeOff } from "lucide-react";
import { useContext, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../../store/auth/AuthContext";
import { type RegisterFormData, registerSchema } from "./RegisterSchema";
import { registerUser } from "./UserService";

export default function RegisterForm({
	className,
	...props
}: React.ComponentProps<"div">) {
	const {
		register,
		handleSubmit,
		control,
		formState: { errors, isSubmitting },
	} = useForm<RegisterFormData>({
		resolver: zodResolver(registerSchema),
	});
	const [error, setError] = useState<string>("");
	const [showPassword, setShowPassword] = useState(false);
	const [showConfirmPassword, setShowConfirmPassword] = useState(false);
	const authContext = useContext(AuthContext);
	const navigate = useNavigate();
	const countryOptions = getCountryOptions();

	const onSubmit = async (data: RegisterFormData) => {
		try {
			setError("");
			const { access_token } = await registerUser(
				data.email,
				data.password,
				data.first_name,
				data.country_code,
			);
			authContext?.login(access_token);
			navigate("/");
		} catch (error) {
			setError(error instanceof Error ? error.message : "Registration failed");
			console.error("Registration failed", error);
		}
	};

	return (
		<PageLayout variant="default" className={className} {...props}>
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Register</CardTitle>
					<CardDescription>Create a new account to get started</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <div className="mb-4 text-sm text-red-500">{error}</div>}
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
										onClick={() => setShowPassword(!showPassword)}
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
										onClick={() => setShowConfirmPassword(!showConfirmPassword)}
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
								<Label htmlFor="country_code">Country</Label>
								<Controller
									control={control}
									name="country_code"
									render={({ field }) => {
										const [open, setOpen] = useState(false);

										return (
											<Popover open={open} onOpenChange={setOpen}>
												<PopoverTrigger asChild>
													<Button // biome-ignore lint/a11y/useSemanticElements: This is a valid ARIA pattern for a custom combobox
														variant="outline"
														role="combobox"
														aria-expanded={open}
														aria-haspopup="listbox"
														className="w-full justify-between"
													>
														{field.value
															? countryOptions.find(
																	(country) => country.value === field.value,
																)?.label
															: "Select country..."}
														<ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
													</Button>
												</PopoverTrigger>
												<PopoverContent className="w-full p-0">
													<Command>
														<CommandInput placeholder="Search country..." />
														<CommandEmpty>No country found.</CommandEmpty>
														<CommandGroup className="max-h-64 overflow-y-auto">
															{countryOptions.map((country) => (
																<CommandItem
																	key={country.value}
																	value={country.value}
																	onSelect={(currentValue) => {
																		field.onChange(currentValue);
																		setOpen(false);
																	}}
																>
																	<Check
																		className={`mr-2 h-4 w-4 ${
																			field.value === country.value
																				? "opacity-100"
																				: "opacity-0"
																		}`}
																	/>
																	{country.label}
																</CommandItem>
															))}
														</CommandGroup>
													</Command>
												</PopoverContent>
											</Popover>
										);
									}}
								/>
								{errors.country_code && (
									<p className="text-sm text-red-500">
										{errors.country_code.message}
									</p>
								)}
							</div>

							<div className="flex flex-col gap-3">
								<Button
									type="submit"
									disabled={isSubmitting}
									className="w-full"
								>
									{isSubmitting ? "Registering..." : "Register"}
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
