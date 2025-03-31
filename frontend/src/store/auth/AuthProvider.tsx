import api from "@/services/api";
import { type ReactNode, useEffect, useState } from "react";
import { toast } from "sonner";
import { AuthContext, type TokenPair } from "./AuthContext";
import {
	clearAuthFromIndexedDB,
	loadAuthFromIndexedDB,
	saveAuthToIndexedDB,
} from "./authDB";

interface IAuthProvider {
	children: ReactNode;
}

export function AuthProvider({ children }: IAuthProvider) {
	const [accessToken, setAccessToken] = useState<string | null>(null);
	const [refreshToken, setRefreshToken] = useState<string | null>(null);
	const [isAuthenticated, setIsAuthenticated] = useState(false);
	const [firstName, setFirstName] = useState<string | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [hasLoggedOut, setHasLoggedOut] = useState(false);

	useEffect(() => {
		const loadAuthState = async () => {
			const localAccessToken = localStorage.getItem("access_token");
			const localRefreshToken = localStorage.getItem("refresh_token");
			const localFirstName = localStorage.getItem("first_name");

			if (localAccessToken && localRefreshToken) {
				setAccessToken(localAccessToken);
				setRefreshToken(localRefreshToken);
				setIsAuthenticated(true);
				if (localFirstName) {
					setFirstName(localFirstName);
				}
			} else {
				const indexedDBAuth = await loadAuthFromIndexedDB();

				if (indexedDBAuth.access_token && indexedDBAuth.refresh_token) {
					setAccessToken(indexedDBAuth.access_token);
					setRefreshToken(indexedDBAuth.refresh_token);
					setIsAuthenticated(indexedDBAuth.isAuthenticated);
					if (indexedDBAuth.firstName) {
						setFirstName(indexedDBAuth.firstName);
					}

					localStorage.setItem("access_token", indexedDBAuth.access_token);
					localStorage.setItem("refresh_token", indexedDBAuth.refresh_token);
					if (indexedDBAuth.firstName) {
						localStorage.setItem("first_name", indexedDBAuth.firstName);
					}
				}
			}

			if (import.meta.env.DEV && import.meta.env.VITE_FORCE_AUTH === "true") {
				setIsAuthenticated(true);
			}

			setIsLoading(false);
		};

		loadAuthState();
	}, []);

	useEffect(() => {
		if (hasLoggedOut) {
			setIsAuthenticated(false);
		}
	}, [hasLoggedOut]);

	const login = async (tokenPair: TokenPair, userFirstName?: string) => {
		setAccessToken(tokenPair.access_token);
		setRefreshToken(tokenPair.refresh_token);
		setIsAuthenticated(true);
		setHasLoggedOut(false);

		localStorage.setItem("access_token", tokenPair.access_token);
		localStorage.setItem("refresh_token", tokenPair.refresh_token);

		if (userFirstName) {
			setFirstName(userFirstName);
			localStorage.setItem("first_name", userFirstName);
			await saveAuthToIndexedDB({
				...tokenPair,
				firstName: userFirstName,
				isAuthenticated: true,
			});

			toast.success(`Welcome, ${userFirstName}!`, {
				description: "You've successfully logged in",
				duration: 3000,
			});
		} else {
			await saveAuthToIndexedDB({
				...tokenPair,
				isAuthenticated: true,
			});
		}
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

			await saveAuthToIndexedDB({
				...response.data,
				firstName,
				isAuthenticated: true,
			});

			return true;
		} catch (error) {
			logout();
			return false;
		}
	};

	const logout = async () => {
		const currentFirstName = firstName;

		if (currentFirstName) {
			toast.success(`Goodbye, ${currentFirstName}`, {
				description: "You've been successfully logged out",
				duration: 3000,
			});
		}

		setAccessToken(null);
		setRefreshToken(null);
		setFirstName(null);
		setIsAuthenticated(false);
		setHasLoggedOut(true);

		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
		localStorage.removeItem("first_name");

		await clearAuthFromIndexedDB();
	};

	if (isLoading) {
		return null;
	}

	return (
		<AuthContext.Provider
			value={{
				accessToken,
				refreshToken,
				isAuthenticated,
				firstName,
				login,
				logout,
				refreshAccessToken,
			}}
		>
			{children}
		</AuthContext.Provider>
	);
}
