import { Route, Routes } from "react-router-dom";
import { LoginForm } from "../features/user/LoginForm";
import ProtectedRoute from "./ProtectedRoute";
import RegisterForm from "@/features/user/RegisterForm";
// import NotFound from "../components/NotFound";

const AppRoutes = () => {
	return (
		<Routes>
			{/* Public routes */}
			<Route path="/login" element={<LoginForm />} />
			<Route path="/register" element={<RegisterForm />} />

			{/* Protected routes */}
			<Route
				path="/"
				element={
					<ProtectedRoute>
						{/* Replace this with your home component */}
						<div>Home Page</div>
					</ProtectedRoute>
				}
			/>

			{/* Undefined route */}
			{/* <Route path="*" element={<NotFound />} /> */}
		</Routes>
	);
};

export default AppRoutes;
