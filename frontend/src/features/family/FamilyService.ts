import api, { handleApiError } from "@/services/api";
import { formatError } from "@/utils/errorUtils";
import axios from "axios";
import { apiCache } from "@/services/apiCache"; // <-- import cache

const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";

export const FAMILY_SERVICE_ERRORS = {
	FETCH_BOTANICAL_GROUPS_FAILED:
		"Failed to fetch botanical groups. Please try again.",
	SERVER_ERROR: "Server error. Please try again later.",
	NETWORK_ERROR: "Network error. Please check your connection and try again.",
	UNKNOWN_ERROR: "An unexpected error occurred. Please try again.",
	format: formatError,
};

export interface IFamily {
	id: string;
	name: string;
}

export interface IBotanicalGroup {
	id: string;
	name: string;
	recommended_rotation_years: number | null;
	families: IFamily[];
}

export interface IFamilyInfo {
	id: string;
	name: string;
	botanical_group: {
		id: string;
		name: string;
		recommended_rotation_years: number | null;
	};
	pests?: Array<{
		id: string;
		name: string;
		treatments?: Array<{ id: string; name: string }>;
		preventions?: Array<{ id: string; name: string }>;
	}>;
	diseases?: Array<{
		id: string;
		name: string;
		symptoms?: Array<{ id: string; name: string }>;
		treatments?: Array<{ id: string; name: string }>;
		preventions?: Array<{ id: string; name: string }>;
	}>;
	antagonises?: Array<{ id: string; name: string }>;
	companion_to?: Array<{ id: string; name: string }>;
}

export async function getBotanicalGroups(
	signal?: AbortSignal,
): Promise<IBotanicalGroup[] | null> {
	const cacheKey = "botanicalGroups";
	const isTest = import.meta.env.MODE === "test";
	if (!isTest) {
		const cached = apiCache.get<IBotanicalGroup[]>(cacheKey);
		if (cached) return cached;
	}

	try {
		const response = await api.get<IBotanicalGroup[]>(
			`${API_PREFIX}/families/botanical-groups/`,
			{
				signal,
			},
		);

		if (Array.isArray(response.data) && response.data.length === 0) {
			return [];
		}

		if (!Array.isArray(response.data)) {
			return null;
		}

		const groups = response.data.map((group) => ({
			...group,
			recommended_rotation_years:
				group.recommended_rotation_years === null
					? null
					: group.recommended_rotation_years,
		}));

		if (groups.length > 0 && !isTest) {
			apiCache.set(cacheKey, groups);
		}
		return groups;
	} catch (error) {
		if (axios.isCancel(error)) {
			throw error;
		}

		if (axios.isAxiosError(error)) {
			if (error.response) {
				switch (error.response.status) {
					case 500:
						throw new Error(FAMILY_SERVICE_ERRORS.SERVER_ERROR);
					default:
						throw new Error(
							FAMILY_SERVICE_ERRORS.format(error.response.data) ||
								FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR,
						);
				}
			}
			if (error.request) {
				throw new Error(FAMILY_SERVICE_ERRORS.NETWORK_ERROR);
			}
		}

		throw new Error(FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR);
	}
}

export async function getFamilyInfo(
	familyId: string,
	signal?: AbortSignal,
): Promise<IFamilyInfo> {
	const cacheKey = `familyInfo:${familyId}`;
	const cached = apiCache.get<IFamilyInfo>(cacheKey);
	if (cached) return cached;

	try {
		const data = await api.cachedGet<IFamilyInfo>(
			`/families/${familyId}/info`,
			{ signal },
		);
		apiCache.set(cacheKey, data);
		return data;
	} catch (error) {
		if (axios.isCancel(error)) throw error;
		throw new Error(
			FAMILY_SERVICE_ERRORS.format(error) ||
				FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR,
		);
	}
}

export async function getFamilyDetails(familyId: string, signal?: AbortSignal) {
	try {
		const response = await api.get(
			`/families/${familyId}/`,
			signal ? { signal } : undefined,
		);

		if (response.data && response.data.detail === "Family not found") {
			throw new Error("Family not found");
		}

		return response.data;
	} catch (error: unknown) {
		if (
			typeof error === "object" &&
			error !== null &&
			"response" in error &&
			(error as { response?: { status?: number } }).response?.status === 404
		) {
			throw new Error("Family not found");
		}
		if (error instanceof Error && error.message === "Family not found") {
			throw error;
		}
		throw error;
	}
}
