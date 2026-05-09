import type { ITokenPair } from "@/store/auth/AuthContext";

let accessToken: string | null = null;
let refreshToken: string | null = null;

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

const getStorage = (): Storage | null => {
	if (globalThis.window === undefined) {
		return null;
	}

	return globalThis.localStorage;
};

const hydrateTokensFromStorage = (): void => {
	if (accessToken && refreshToken) {
		return;
	}

	const storage = getStorage();
	if (!storage) {
		return;
	}

	accessToken = storage.getItem(ACCESS_TOKEN_KEY);
	refreshToken = storage.getItem(REFRESH_TOKEN_KEY);
};

const persistTokens = (tokenPair: ITokenPair): void => {
	const storage = getStorage();
	if (!storage) {
		return;
	}

	storage.setItem(ACCESS_TOKEN_KEY, tokenPair.access_token);
	storage.setItem(REFRESH_TOKEN_KEY, tokenPair.refresh_token);
};

const clearPersistedTokens = (): void => {
	const storage = getStorage();
	if (!storage) {
		return;
	}

	storage.removeItem(ACCESS_TOKEN_KEY);
	storage.removeItem(REFRESH_TOKEN_KEY);
};

export const tokenStore = {
	getAccessToken(): string | null {
		hydrateTokensFromStorage();
		return accessToken;
	},

	getRefreshToken(): string | null {
		hydrateTokensFromStorage();
		return refreshToken;
	},

	getTokens(): ITokenPair | null {
		hydrateTokensFromStorage();
		if (!accessToken || !refreshToken) {
			return null;
		}

		return {
			access_token: accessToken,
			refresh_token: refreshToken,
		};
	},

	setTokens(tokenPair: ITokenPair): void {
		accessToken = tokenPair.access_token;
		refreshToken = tokenPair.refresh_token;
		persistTokens(tokenPair);
	},

	clearTokens(): void {
		accessToken = null;
		refreshToken = null;
		clearPersistedTokens();
	},
};
