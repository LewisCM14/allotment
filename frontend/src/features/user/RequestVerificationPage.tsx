// import { FormError } from "@/components/FormError";
// import { PageLayout } from "@/components/layouts/PageLayout";
// import { Button } from "@/components/ui/Button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
// import { Input } from "@/components/ui/Input";
// import { Label } from "@/components/ui/Label";
// import { useToast } from "@/components/ui/Sonner";
// import { requestVerificationEmail } from "@/features/user/UserService";
// import { zodResolver } from "@hookform/resolvers/zod";
// import { useState } from "react";
// import { useForm } from "react-hook-form";
// import { Link } from "react-router-dom";
// import { z } from "zod";

// const requestVerificationSchema = z.object({
// 	email: z.string().email("Please enter a valid email address"),
// });

// type RequestVerificationFormData = z.infer<typeof requestVerificationSchema>;

// export default function RequestVerificationPage() {
// 	const [submitted, setSubmitted] = useState(false);
// 	const [error, setError] = useState("");
// 	const { toast } = useToast();
// 	const {
// 		register,
// 		handleSubmit,
// 		formState: { errors, isSubmitting },
// 	} = useForm<RequestVerificationFormData>({
// 		resolver: zodResolver(requestVerificationSchema),
// 		mode: "onBlur",
// 	});

// 	const onSubmit = async (data: RequestVerificationFormData) => {
// 		try {
// 			setError("");
// 			await requestVerificationEmail(data.email);
// 			setSubmitted(true);
// 			toast({
// 				title: "Verification email sent",
// 				description: "Please check your inbox for the verification link",
// 			});
// 		} catch (err) {
// 			setError(
// 				err instanceof Error
// 					? err.message
// 					: "Failed to send verification email",
// 			);
// 			toast({
// 				title: "Request failed",
// 				description: "There was a problem sending the verification email",
// 				variant: "destructive",
// 			});
// 		}
// 	};

// 	return (
// 		<PageLayout variant="default">
// 			<Card className="w-full max-w-md mx-auto">
// 				<CardHeader>
// 					<CardTitle>Request Verification Email</CardTitle>
// 				</CardHeader>
// 				<CardContent>
// 					{!submitted ? (
// 						<form onSubmit={handleSubmit(onSubmit)}>
// 							{error && <FormError message={error} className="mb-4" />}
// 							<div className="grid gap-4">
// 								<div className="grid gap-2">
// 									<Label htmlFor="email">Email Address</Label>
// 									<Input
// 										{...register("email")}
// 										id="email"
// 										placeholder="Enter your email address"
// 										type="email"
// 									/>
// 									{errors.email && (
// 										<p className="text-sm text-red-500">
// 											{errors.email.message}
// 										</p>
// 									)}
// 								</div>
// 								<Button type="submit" disabled={isSubmitting}>
// 									{isSubmitting ? "Sending..." : "Send Verification Email"}
// 								</Button>
// 							</div>
// 						</form>
// 					) : (
// 						<div className="flex flex-col items-center py-4 gap-4 text-center">
// 							<h2 className="text-xl font-semibold">Verification Email Sent</h2>
// 							<p className="text-gray-600">
// 								We've sent a verification link to your email address. Please
// 								check your inbox and click on the link to verify your account.
// 							</p>
// 							<div className="flex flex-col gap-2 mt-4 w-full">
// 								<Button variant="outline" asChild>
// 									<Link to="/">Return to Home</Link>
// 								</Button>
// 							</div>
// 						</div>
// 					)}
// 				</CardContent>
// 			</Card>
// 		</PageLayout>
// 	);
// }
