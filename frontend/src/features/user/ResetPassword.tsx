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
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { requestPasswordReset } from "./UserService";

const resetSchema = z.object({
	email: z
		.string()
		.email("Please enter a valid email address")
		.min(1, "Email is required"),
});

type ResetFormData = z.infer<typeof resetSchema>;

export default function ResetPassword() {
	const {
		register,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<ResetFormData>({
		resolver: zodResolver(resetSchema),
		mode: "onBlur",
	});

	const [error, setError] = useState<string>("");
	const [success, setSuccess] = useState<string>("");
	const [isOffline, setIsOffline] = useState(!navigator.onLine);

	const onSubmit = async (data: ResetFormData) => {
		try {
			setError("");
			setSuccess("");

			if (isOffline) {
				setError(
					"You are offline. Please connect to the internet to continue.",
				);
				return;
			}

			const result = await requestPasswordReset(data.email);
			setSuccess(result.message);
		} catch (err) {
			if (err instanceof Error) {
				setError(err.message);
			} else {
				setError("An unexpected error occurred. Please try again.");
			}
			console.error("Password reset request failed", err);
		}
	};

	return (
		<PageLayout variant="default">
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Reset Password</CardTitle>
					<CardDescription>
						Enter your email address and we'll send you a link to reset your
						password
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <FormError message={error} className="mb-4" />}
						{success && (
							<div className="p-3 mb-4 text-green-800 bg-green-50 rounded border border-green-200">
								<p>{success}</p>
							</div>
						)}

						{isOffline && (
							<div className="p-3 mb-4 text-amber-800 bg-amber-50 rounded border border-amber-200">
								<p>
									You are currently offline. This feature requires an internet
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

							<div className="flex flex-col gap-3">
								<Button
									type="submit"
									disabled={isSubmitting || isOffline}
									className="w-full"
								>
									{isSubmitting ? "Sending..." : "Send Reset Link"}
								</Button>
							</div>
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
