import { useAuth } from "@/store/auth/AuthContext";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

export function useLogout() {
	const { logout: authLogout } = useAuth();
	const queryClient = useQueryClient();
	const navigate = useNavigate();

	return useCallback(async () => {
		try {
			await authLogout();
			queryClient.clear();
			navigate("/login");
		} catch (error) {
			console.error("Error during logout:", error);
			queryClient.clear();
			navigate("/login");
		}
	}, [authLogout, queryClient, navigate]);
}
