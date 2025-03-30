import { openDB } from "idb";
import type { TokenPair } from "./AuthContext";

const DB_NAME = "allotment-auth";
const STORE_NAME = "auth";
const VERSION = 1;

export const initAuthDB = async () => {
	return openDB(DB_NAME, VERSION, {
		upgrade(db) {
			if (!db.objectStoreNames.contains(STORE_NAME)) {
				db.createObjectStore(STORE_NAME);
			}
		},
	});
};

export const saveAuthToIndexedDB = async (tokenPair: TokenPair) => {
	try {
		const db = await initAuthDB();
		await db.put(STORE_NAME, tokenPair.access_token, "access_token");
		await db.put(STORE_NAME, tokenPair.refresh_token, "refresh_token");
		await db.put(STORE_NAME, true, "isAuthenticated");
		return true;
	} catch (error) {
		console.error("Failed to save auth to IndexedDB:", error);
		return false;
	}
};

export const loadAuthFromIndexedDB = async () => {
	try {
		const db = await initAuthDB();
		const access_token = await db.get(STORE_NAME, "access_token");
		const refresh_token = await db.get(STORE_NAME, "refresh_token");
		const isAuthenticated = await db.get(STORE_NAME, "isAuthenticated");

		return {
			access_token: access_token || null,
			refresh_token: refresh_token || null,
			isAuthenticated: isAuthenticated || false,
		};
	} catch (error) {
		console.error("Failed to load auth from IndexedDB:", error);
		return {
			access_token: null,
			refresh_token: null,
			isAuthenticated: false,
		};
	}
};

export const clearAuthFromIndexedDB = async () => {
	try {
		const db = await initAuthDB();
		await db.delete(STORE_NAME, "access_token");
		await db.delete(STORE_NAME, "refresh_token");
		await db.delete(STORE_NAME, "isAuthenticated");
		return true;
	} catch (error) {
		console.error("Failed to clear auth from IndexedDB:", error);
		return false;
	}
};
