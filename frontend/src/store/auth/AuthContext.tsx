import type { IUserData } from "@/features/user/services/UserService";
import { createContext, useContext } from "react";

export interface ITokenPair {
	access_token: string;
	refresh_token: string;
}

export interface IUser {
	user_id: string;
	user_first_name: string;
	user_email: string;
	isEmailVerified: boolean;
}

export interface IAuthContext {
	accessToken: string | null;
	refreshToken: string | null;
	isAuthenticated: boolean;
	firstName: string | null;
	user: IUser | null;
	login: (
		tokenPair: ITokenPair,
		firstName?: string,
		userData?: IUserData,
	) => Promise<void>;
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
