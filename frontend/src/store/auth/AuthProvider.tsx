import type { IUserData } from "@/features/auth/services/AuthService";
import api from "@/services/api";
import { API_VERSION } from "@/services/apiConfig";
import { tokenStore } from "@/services/tokenStore";
import {
	type ReactNode,
	useCallback,
	useEffect,
	useMemo,
	useState,
} from "react";
import { errorMonitor } from "@/services/errorMonitoring";
import { lazyToast } from "@/utils/lazyToast";
import { AuthContext, type ITokenPair, type IUser } from "./AuthContext";
import { clearAuthFromIndexedDB } from "./authDB";

interface IAuthProvider {
	readonly children: ReactNode;
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
		const hydrateProfileFromLocalStorage = () => {
			const firstName = localStorage.getItem("first_name");
			if (firstName) {
				setFirstName(firstName);
				const email = localStorage.getItem("user_email");
				const userId = localStorage.getItem("user_id");
				const emailVerified = localStorage.getItem("is_email_verified");
				if (email) {
					setUser({
						user_id: userId ?? "",
						user_first_name: firstName,
						user_email: email,
						isEmailVerified: emailVerified === "true",
					});
				}
			}
		};

		const loadAuthState = async () => {
			localStorage.removeItem("access_token");
			localStorage.removeItem("refresh_token");

			try {
				await clearAuthFromIndexedDB();
			} catch (error) {
				errorMonitor.captureException(error, {
					context: "clear_legacy_auth_state",
				});
			}

			const tokens = tokenStore.getTokens();
			if (tokens) {
				setAccessToken(tokens.access_token);
				setRefreshToken(tokens.refresh_token);
				setIsAuthenticated(true);
				hydrateProfileFromLocalStorage();
			}

			if (import.meta.env.DEV && import.meta.env.VITE_FORCE_AUTH === "true") {
				setIsAuthenticated(true);
			}

			setIsLoading(false);
		};

		void loadAuthState();
	}, []);

	useEffect(() => {
		if (hasLoggedOut) {
			setIsAuthenticated(false);
		}
	}, [hasLoggedOut]);

	const login = useCallback(
		async (
			tokenPair: ITokenPair,
			userFirstName?: string,
			userData?: IUserData,
		) => {
			tokenStore.setTokens(tokenPair);
			setAccessToken(tokenPair.access_token);
			setRefreshToken(tokenPair.refresh_token);
			setIsAuthenticated(true);
			setHasLoggedOut(false);

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

				lazyToast.success(`Welcome, ${userFirstName}!`, {
					description: "You've successfully logged in",
					duration: 3000,
				});
			}
		},
		[],
	);

	const logout = useCallback(async () => {
		const currentFirstName = firstName;

		if (currentFirstName) {
			lazyToast.success(`Goodbye, ${currentFirstName}`, {
				description: "You've been successfully logged out",
				duration: 3000,
			});
		}

		tokenStore.clearTokens();
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
	}, [firstName]);

	const refreshAccessToken = useCallback(async (): Promise<boolean> => {
		try {
			if (!refreshToken) {
				return false;
			}

			const response = await api.post<ITokenPair>(
				`${API_VERSION}/user/auth/refresh`,
				{ refresh_token: refreshToken },
			);

			tokenStore.setTokens(response.data);
			setAccessToken(response.data.access_token);
			setRefreshToken(response.data.refresh_token);

			return true;
		} catch (error: unknown) {
			errorMonitor.captureException(error, { context: "refreshAccessToken" });

			// Check if it's an API error with status code
			if (error && typeof error === "object" && "response" in error) {
				const apiError = error as { response?: { status?: number } };
				if (apiError.response?.status === 401) {
					lazyToast.error("Your session has expired, please log in again");
				} else {
					lazyToast.error("Failed to refresh authentication");
				}
			} else {
				lazyToast.error("Network error while refreshing authentication");
			}

			logout();
			return false;
		}
	}, [refreshToken, logout]);

	const authContextValue = useMemo(
		() => ({
			accessToken,
			refreshToken,
			isAuthenticated,
			firstName,
			user,
			login,
			logout,
			refreshAccessToken,
		}),
		[
			accessToken,
			refreshToken,
			isAuthenticated,
			firstName,
			user,
			login,
			logout,
			refreshAccessToken,
		],
	);

	if (isLoading) {
		return null;
	}

	return (
		<AuthContext.Provider value={authContextValue}>
			{children}
		</AuthContext.Provider>
	);
}
