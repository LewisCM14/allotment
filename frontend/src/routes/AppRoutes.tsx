import { Progress } from "@/components/ui/Progress";
import React, { Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";

const LoginForm = React.lazy(() => import("../features/user/LoginForm"));
const RegisterForm = React.lazy(() => import("../features/user/RegisterForm"));
const EmailVerificationPage = React.lazy(
	() => import("../features/user/EmailVerification"),
);
// const RequestVerificationPage = React.lazy(
// 	() => import("../features/user/RequestVerificationPage"),
// );
const NotFound = React.lazy(() => import("../components/NotFound"));
// const HomePage = React.lazy(() => import("../features/home/HomePage"));

const AppRoutes = () => {
	return (
		<Suspense fallback={<Progress value={100} className="w-full" />}>
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
				<Route path="/verify-email" element={<EmailVerificationPage />} />

				{/* Protected routes - only for authenticated users */}
				{/* <Route
					path="/request-verification"
					element={
						<ProtectedRoute>
							<RequestVerificationPage />
						</ProtectedRoute>
					}
				/> */}

				<Route
					path="/"
					element={
						<ProtectedRoute>
							{/* Replace this with your home component */}
							<div>Home Page</div>
						</ProtectedRoute>
					}
				/>

				{/* Undefined route - catches all other routes */}
				<Route
					path="*"
					element={
						<Suspense fallback={<div>Loading Not Found...</div>}>
							<NotFound />
						</Suspense>
					}
				/>
			</Routes>
		</Suspense>
	);
};

export default AppRoutes;
