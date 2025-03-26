import { createContext, useContext } from "react";

export interface IAuthContext {
	token: string | null;
	isAuthenticated: boolean;
	login: (token: string) => void;
	logout: () => void;
}

export const AuthContext = createContext<IAuthContext | undefined>(undefined);

export function useAuth() {
	const context = useContext(AuthContext);
	if (context === undefined) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}
