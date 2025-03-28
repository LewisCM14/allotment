import RegisterForm from "@/features/user/RegisterForm";
import { Route, Routes } from "react-router-dom";
import { LoginForm } from "../features/user/LoginForm";
import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";
// import NotFound from "../components/NotFound";

const AppRoutes = () => {
	return (
		<Routes>
			{/* Public routes - only for non-authenticated users */}
			<Route
				path="/login"
				element={
					<PublicRoute>
						<LoginForm />
					</PublicRoute>
				}
			/>
			<Route
				path="/register"
				element={
					<PublicRoute>
						<RegisterForm />
					</PublicRoute>
				}
			/>

			{/* Protected routes - only for authenticated users */}
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
