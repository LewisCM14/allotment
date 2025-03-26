import { useAuth } from "@/store/auth/AuthContext";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

export function useLogout() {
	const { logout: authLogout } = useAuth();
	const queryClient = useQueryClient();
	const navigate = useNavigate();

	return () => {
		authLogout();
		queryClient.clear();
		navigate("/login");
	};
}
