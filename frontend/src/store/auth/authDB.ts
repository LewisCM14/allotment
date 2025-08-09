import { openDB } from "idb";
import type { ITokenPair } from "./AuthContext";
import { errorMonitor } from "@/services/errorMonitoring";

interface IAuthState extends ITokenPair {
	isAuthenticated: boolean;
	firstName?: string | null;
}

const dbPromise = openDB("auth-store", 1, {
	upgrade(db) {
		db.createObjectStore("auth");
	},
});

export async function saveAuthToIndexedDB(auth: IAuthState): Promise<void> {
	const db = await dbPromise;
	await db.put("auth", auth, "authState");
}

export async function loadAuthFromIndexedDB(): Promise<IAuthState> {
	try {
		const db = await dbPromise;
		const authState = await db.get("auth", "authState");
		return (
			authState ?? {
				access_token: "",
				refresh_token: "",
				isAuthenticated: false,
			}
		);
	} catch (error) {
		errorMonitor.captureException(error, { context: "loadAuthFromIndexedDB" });
		return { access_token: "", refresh_token: "", isAuthenticated: false };
	}
}

export async function clearAuthFromIndexedDB(): Promise<void> {
	const db = await dbPromise;
	await db.delete("auth", "authState");
}
