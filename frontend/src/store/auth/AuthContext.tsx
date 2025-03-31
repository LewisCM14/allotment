import { createContext, useContext } from "react";

export interface TokenPair {
	access_token: string;
	refresh_token: string;
}

export interface IAuthContext {
	accessToken: string | null;
	refreshToken: string | null;
	isAuthenticated: boolean;
	firstName: string | null;
	login: (tokenPair: TokenPair, firstName?: string) => Promise<void>;
	logout: () => Promise<void>;
	refreshAccessToken: () => Promise<boolean>;
}

export const AuthContext = createContext<IAuthContext | undefined>(undefined);

export function useAuth() {
	const context = useContext(AuthContext);
	if (context === undefined) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}
