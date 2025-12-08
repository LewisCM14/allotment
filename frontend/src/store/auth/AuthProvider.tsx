import type { IUserData } from "@/features/auth/services/AuthService";
import api from "@/services/api";
import { API_VERSION } from "@/services/apiConfig";
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
import {
	clearAuthFromIndexedDB,
	loadAuthFromIndexedDB,
	saveAuthToIndexedDB,
} from "./authDB";

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
		const loadAuthFromLocalStorage = () => {
			const accessToken = localStorage.getItem("access_token");
			const refreshToken = localStorage.getItem("refresh_token");
			if (!accessToken || !refreshToken) return false;

			setAccessToken(accessToken);
			setRefreshToken(refreshToken);
			setIsAuthenticated(true);

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
			return true;
		};

		const loadAuthFromDbAndSync = async () => {
			const dbAuth = await loadAuthFromIndexedDB();
			if (!dbAuth.access_token || !dbAuth.refresh_token) return;

			setAccessToken(dbAuth.access_token);
			setRefreshToken(dbAuth.refresh_token);
			setIsAuthenticated(dbAuth.isAuthenticated);
			if (dbAuth.firstName) {
				setFirstName(dbAuth.firstName);
			}

			localStorage.setItem("access_token", dbAuth.access_token);
			localStorage.setItem("refresh_token", dbAuth.refresh_token);
			if (dbAuth.firstName) {
				localStorage.setItem("first_name", dbAuth.firstName);
			}
		};

		const loadAuthState = async () => {
			const loadedFromLocal = loadAuthFromLocalStorage();
			if (!loadedFromLocal) {
				await loadAuthFromDbAndSync();
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

	const login = useCallback(
		async (
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

				lazyToast.success(`Welcome, ${userFirstName}!`, {
					description: "You've successfully logged in",
					duration: 3000,
				});
			} else {
				await saveAuthToIndexedDB({
					...tokenPair,
					isAuthenticated: true,
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
	}, [refreshToken, firstName, logout]);

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
