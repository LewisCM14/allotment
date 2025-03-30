import { Navigate } from "react-router-dom";
import { useAuth } from "../store/auth/AuthContext";

interface IPublicRoute {
	children: React.ReactNode;
}

const PublicRoute = ({ children }: IPublicRoute) => {
	const { isAuthenticated } = useAuth();

	if (isAuthenticated) {
		return <Navigate to="/" replace />;
	}

	return <>{children}</>;
};

export default PublicRoute;
