import { useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useState } from "react";

interface AuthContextType {
	token: string | null;
	login: (token: string) => void;
	logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
	const [token, setToken] = useState<string | null>(
		localStorage.getItem("token"),
	);
	const queryClient = useQueryClient();

	const login = (token: string) => {
		setToken(token);
		localStorage.setItem("token", token);
	};

	const logout = () => {
		setToken(null);
		localStorage.removeItem("token");
		queryClient.clear();
	};

	return (
		<AuthContext.Provider value={{ token, login, logout }}>
			{children}
		</AuthContext.Provider>
	);
};
