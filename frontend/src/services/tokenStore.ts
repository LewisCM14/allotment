import type { ITokenPair } from "@/store/auth/AuthContext";

let accessToken: string | null = null;
let refreshToken: string | null = null;

export const tokenStore = {
	getAccessToken(): string | null {
		return accessToken;
	},

	getRefreshToken(): string | null {
		return refreshToken;
	},

	getTokens(): ITokenPair | null {
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
	},

	clearTokens(): void {
		accessToken = null;
		refreshToken = null;
	},
};
