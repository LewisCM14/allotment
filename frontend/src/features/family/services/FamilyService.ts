import api, { handleApiError } from "@/services/api";
import { formatError } from "@/utils/errorUtils";
import axios from "axios";

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
): Promise<IBotanicalGroup[]> {
	try {
		const response = await api.cachedGet<IBotanicalGroup[]>(
			"/families/botanical-groups/",
			{ signal },
		);

		// Handle null or malformed response
		if (!Array.isArray(response)) {
			return [];
		}

		return response.map((group) => ({
			...group,
			recommended_rotation_years: group.recommended_rotation_years ?? null,
		}));
	} catch (error: unknown) {
		if (axios.isCancel(error)) throw error;
		return handleApiError(
			error,
			FAMILY_SERVICE_ERRORS.FETCH_BOTANICAL_GROUPS_FAILED,
		);
	}
}

export async function getFamilyInfo(
	familyId: string,
	signal?: AbortSignal,
): Promise<IFamilyInfo> {
	try {
		const data = await api.cachedGet<IFamilyInfo>(
			`/families/${familyId}/info`,
			{ signal },
		);
		return data;
	} catch (error: unknown) {
		if (axios.isCancel(error)) throw error;
		return handleApiError(error, FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR);
	}
}

export async function getFamilyDetails(familyId: string, signal?: AbortSignal) {
	try {
		const response = await api.get(
			`/families/${familyId}`,
			signal ? { signal } : undefined,
		);

		if (response.data && response.data.detail === "Family not found") {
			throw new Error("Family not found");
		}

		return response.data;
	} catch (error: unknown) {
		if (axios.isCancel(error)) throw error;
		return handleApiError(error, "Failed to fetch family details");
	}
}
