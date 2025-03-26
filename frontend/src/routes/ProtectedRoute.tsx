import { Navigate } from "react-router-dom";
import { useAuth } from "../store/auth/AuthContext";

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
