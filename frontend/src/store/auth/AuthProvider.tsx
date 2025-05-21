import type { IUserData } from "@/features/user/UserService";
import api from "@/services/api";
import { type ReactNode, useEffect, useState } from "react";
import { toast } from "sonner";
import { AuthContext, type ITokenPair, type IUser } from "./AuthContext";
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
	const [user, setUser] = useState<IUser | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [hasLoggedOut, setHasLoggedOut] = useState(false);

	useEffect(() => {
		const loadAuthState = async () => {
			const localAccessToken = localStorage.getItem("access_token");
			const localRefreshToken = localStorage.getItem("refresh_token");
			const localFirstName = localStorage.getItem("first_name");
			const localEmail = localStorage.getItem("user_email");
			const localUserId = localStorage.getItem("user_id");
			const localEmailVerified = localStorage.getItem("is_email_verified");

			if (localAccessToken && localRefreshToken) {
				setAccessToken(localAccessToken);
				setRefreshToken(localRefreshToken);
				setIsAuthenticated(true);
				if (localFirstName) {
					setFirstName(localFirstName);
				}

				if (localEmail && localFirstName) {
					setUser({
						user_id: localUserId || "",
						user_first_name: localFirstName,
						user_email: localEmail,
						isEmailVerified: localEmailVerified === "true",
					});
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

	const login = async (
		tokenPair: ITokenPair,
		userFirstName?: string,
		userData?: IUserData,
	) => {
		setAccessToken(tokenPair.access_token);
		setRefreshToken(tokenPair.refresh_token);
		setIsAuthenticated(true);
		setHasLoggedOut(false);

		localStorage.setItem("access_token", tokenPair.access_token);
		localStorage.setItem("refresh_token", tokenPair.refresh_token);

		if (userFirstName) {
			setFirstName(userFirstName);
			localStorage.setItem("first_name", userFirstName);
			if (userData) {
				const userObj: IUser = {
					user_id: userData.user_id || "",
					user_first_name: userFirstName,
					user_email: userData.user_email || "",
					isEmailVerified: userData.is_email_verified || false,
				};
				setUser(userObj);

				localStorage.setItem("user_email", userObj.user_email);
				localStorage.setItem("user_id", userObj.user_id);
				localStorage.setItem(
					"is_email_verified",
					String(userObj.isEmailVerified),
				);
			}

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

			const response = await api.post<ITokenPair>(
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
		setUser(null);
		setIsAuthenticated(false);
		setHasLoggedOut(true);

		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
		localStorage.removeItem("first_name");
		localStorage.removeItem("user_email");
		localStorage.removeItem("user_id");
		localStorage.removeItem("is_email_verified");

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
				user,
				login,
				logout,
				refreshAccessToken,
			}}
		>
			{children}
		</AuthContext.Provider>
	);
}
