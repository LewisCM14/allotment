import { useContext } from "react";
import { useForm } from "react-hook-form";
import { AuthContext } from "../../context/AuthContext";
import { loginUser } from "./authService";

interface LoginFormData {
	email: string;
	password: string;
}

const LoginForm = () => {
	const { register, handleSubmit } = useForm<LoginFormData>();
	const authContext = useContext(AuthContext);

	const onSubmit = async (data: LoginFormData) => {
		try {
			const { token } = await loginUser(data.email, data.password);
			authContext?.login(token);
		} catch (error) {
			console.error("Login failed", error);
		}
	};

	return (
		<form onSubmit={handleSubmit(onSubmit)}>
			<input {...register("email")} placeholder="Email" required />
			<input
				{...register("password")}
				type="password"
				placeholder="Password"
				required
			/>
			<button type="submit">Login</button>
		</form>
	);
};

export default LoginForm;
