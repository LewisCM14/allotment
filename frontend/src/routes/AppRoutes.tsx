import React from "react";
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
	() => import("../features/registration/pages/EmailVerification"),
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
const UserPreference = React.lazy(
	() => import("../features/preference/pages/UserPreference"),
);
const GrowGuidePage = React.lazy(
	() => import("../features/grow_guide/pages/GrowGuides"),
);
const TodoPage = React.lazy(() => import("../features/todo/pages/Todo"));
const PublicGrowGuidesPage = React.lazy(
	() => import("../features/grow_guide/pages/PublicGrowGuides"),
);

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
						<TodoPage />
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
			<Route
				path="/preferences"
				element={
					<ProtectedRoute>
						<UserPreference />
					</ProtectedRoute>
				}
			/>
			<Route path="/public/grow-guides" element={<PublicGrowGuidesPage />} />
			<Route path="/public-guides" element={<PublicGrowGuidesPage />} />
			<Route
				path="/grow-guides"
				element={
					<ProtectedRoute>
						<GrowGuidePage />
					</ProtectedRoute>
				}
			/>
			<Route
				path="/grow-guides/:varietyId"
				element={
					<ProtectedRoute>
						<GrowGuidePage />
					</ProtectedRoute>
				}
			/>
			<Route path="/verify-email" element={<EmailVerificationPage />} />

			{/* Page Not Found */}
			<Route path="*" element={<NotFound />} />
		</Routes>
	);
};

export default AppRoutes;
