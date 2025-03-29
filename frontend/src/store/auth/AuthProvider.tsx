import api from "@/services/api";
import { type ReactNode, useEffect, useState } from "react";
import { AuthContext, type TokenPair } from "./AuthContext";

interface IAuthProvider {
	children: ReactNode;
}

export function AuthProvider({ children }: IAuthProvider) {
	const [accessToken, setAccessToken] = useState<string | null>(() => {
		return localStorage.getItem("access_token");
	});

	const [refreshToken, setRefreshToken] = useState<string | null>(() => {
		return localStorage.getItem("refresh_token");
	});

	const [isAuthenticated, setIsAuthenticated] = useState(() => {
		if (import.meta.env.DEV && import.meta.env.VITE_FORCE_AUTH === "true") {
			return true;
		}
		return localStorage.getItem("access_token") !== null;
	});

	const [hasLoggedOut, setHasLoggedOut] = useState(false);

	useEffect(() => {
		if (hasLoggedOut) {
			setIsAuthenticated(false);
		}
	}, [hasLoggedOut]);

	const login = (tokenPair: TokenPair) => {
		setAccessToken(tokenPair.access_token);
		setRefreshToken(tokenPair.refresh_token);
		setIsAuthenticated(true);
		setHasLoggedOut(false);
		localStorage.setItem("access_token", tokenPair.access_token);
		localStorage.setItem("refresh_token", tokenPair.refresh_token);
	};

	const refreshAccessToken = async (): Promise<boolean> => {
		try {
			if (!refreshToken) {
				return false;
			}

			const response = await api.post<TokenPair>(
				`${import.meta.env.VITE_API_VERSION}/user/auth/refresh`,
				{ refresh_token: refreshToken },
			);

			setAccessToken(response.data.access_token);
			setRefreshToken(response.data.refresh_token);
			localStorage.setItem("access_token", response.data.access_token);
			localStorage.setItem("refresh_token", response.data.refresh_token);

			return true;
		} catch (error) {
			logout();
			return false;
		}
	};

	const logout = () => {
		setAccessToken(null);
		setRefreshToken(null);
		setIsAuthenticated(false);
		setHasLoggedOut(true);
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
	};

	return (
		<AuthContext.Provider
			value={{
				accessToken,
				refreshToken,
				isAuthenticated,
				login,
				logout,
				refreshAccessToken,
			}}
		>
			{children}
		</AuthContext.Provider>
	);
}
