import { Progress } from "@/components/ui/Progress";
import React, { Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";

const LoginForm = React.lazy(() => import("../features/auth/forms/LoginForm"));
const RegisterForm = React.lazy(
	() => import("../features/registration/forms/RegisterForm"),
);
const ResetPassword = React.lazy(
	() => import("../features/auth/forms/ResetPassword"),
);
const EmailVerificationPage = React.lazy(
	() => import("../features/user/pages/EmailVerification"),
);
const UserProfile = React.lazy(
	() => import("../features/user/pages/UserProfile"),
);
const NotFound = React.lazy(() => import("../components/NotFound"));
const SetNewPassword = React.lazy(
	() => import("../features/auth/forms/SetNewPassword"),
);
const BotanicalGroupsPage = React.lazy(
	() => import("../features/family/pages/BotanicalGroups"),
);
const FamilyInfoPage = React.lazy(
	() => import("../features/family/pages/FamilyInfo"),
);
const AllotmentPage = React.lazy(
	() => import("../features/allotment/pages/UserAllotmentInfo"),
);

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
				<Route
					path="/reset-password"
					element={
						<PublicRoute>
							<ResetPassword />
						</PublicRoute>
					}
				/>
				<Route
					path="/set-new-password"
					element={
						<PublicRoute>
							<SetNewPassword />
						</PublicRoute>
					}
				/>

				{/* Protected routes - only for authenticated users */}
				<Route
					path="/profile"
					element={
						<ProtectedRoute>
							<UserProfile />
						</ProtectedRoute>
					}
				/>
				<Route
					path="/"
					element={
						<ProtectedRoute>
							{/* Replace this with your home component */}
							<div>Home Page</div>
						</ProtectedRoute>
					}
				/>
				<Route
					path="/botanical_groups"
					element={
						<ProtectedRoute>
							<BotanicalGroupsPage />
						</ProtectedRoute>
					}
				/>
				<Route
					path="/family/:familyId"
					element={
						<ProtectedRoute>
							<FamilyInfoPage />
						</ProtectedRoute>
					}
				/>
				<Route
					path="/allotment"
					element={
						<ProtectedRoute>
							<AllotmentPage />
						</ProtectedRoute>
					}
				/>

				{/* Page Not Found */}
				<Route
					path="*"
					element={
						<Suspense fallback={<div>Loading Not Found...</div>}>
							<NotFound />
						</Suspense>
					}
				/>

				{/* Verify Email */}
				<Route path="/verify-email" element={<EmailVerificationPage />} />
			</Routes>
		</Suspense>
	);
};

export default AppRoutes;
