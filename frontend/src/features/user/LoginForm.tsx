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
import { useContext, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../../store/auth/AuthContext";
import { loginUser } from "./UserService";

interface ILoginFormData {
	email: string;
	password: string;
}

export function LoginForm({
	className,
	...props
}: React.ComponentProps<"div">) {
	const { register, handleSubmit } = useForm<ILoginFormData>();
	const authContext = useContext(AuthContext);
	const [error, setError] = useState<string>("");
	const navigate = useNavigate();

	const onSubmit = async (data: ILoginFormData) => {
		try {
			setError("");
			const { access_token } = await loginUser(data.email, data.password);
			authContext?.login(access_token);
			navigate("/");
		} catch (error) {
			setError(error instanceof Error ? error.message : "Login failed");
			console.error("Login failed", error);
		}
	};

	return (
		<PageLayout variant="default" className={className} {...props}>
			<Card className="w-full">
				<CardHeader>
					<CardTitle>Login</CardTitle>
					<CardDescription>
						Enter your email below to login to your account
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit(onSubmit)}>
						{error && <div className="mb-4 text-sm text-red-500">{error}</div>}
						<div className="flex flex-col gap-6">
							<div className="grid gap-3">
								<Label htmlFor="email">Email</Label>
								<Input
									{...register("email")}
									id="email"
									type="email"
									placeholder="m@example.com"
									autoComplete="email"
									required
								/>
							</div>
							<div className="grid gap-3">
								<div className="flex items-center">
									<Label htmlFor="password">Password</Label>
									{/* <a
										href="#"
										className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
									>
										Forgot your password?
									</a> */}
								</div>
								<Input
									{...register("password")}
									id="password"
									type="password"
									autoComplete="current-password"
									required
								/>
							</div>
							<div className="flex flex-col gap-3">
								<Button type="submit" className="w-full">
									Login
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
