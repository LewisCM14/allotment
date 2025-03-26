import { type ReactNode, useState } from "react";
import { AuthContext } from "./AuthContext";

interface IAuthProvider {
	children: ReactNode;
}

export function AuthProvider({ children }: IAuthProvider) {
	const [token, setToken] = useState<string | null>(() => {
		return localStorage.getItem("token");
	});

	const [isAuthenticated, setIsAuthenticated] = useState(() => {
		if (import.meta.env.DEV && import.meta.env.VITE_FORCE_AUTH === "true") {
			return true;
		}
		return localStorage.getItem("token") !== null;
	});

	const login = (token: string) => {
		setToken(token);
		setIsAuthenticated(true);
		localStorage.setItem("token", token);
	};

	const logout = () => {
		setToken(null);
		setIsAuthenticated(false);
		localStorage.removeItem("token");
	};

	return (
		<AuthContext.Provider value={{ token, isAuthenticated, login, logout }}>
			{children}
		</AuthContext.Provider>
	);
}
