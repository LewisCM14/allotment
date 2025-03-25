import { Navigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";

interface IProtectedRoute {
	children: React.ReactNode;
}

const ProtectedRoute = ({ children }: IProtectedRoute) => {
	const { isAuthenticated } = useAuth();

	if (!isAuthenticated) {
		return <Navigate to="/login" replace />;
	}

	return <>{children}</>;
};

export default ProtectedRoute;
