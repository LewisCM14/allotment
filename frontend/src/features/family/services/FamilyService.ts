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
	id: string; // UUID serialized as string
	name: string;
}

export interface IBotanicalGroup {
	id: string; // UUID serialized as string
	name: string;
	recommended_rotation_years: number | null;
	families: IFamily[];
}

export interface IFamilyInfo {
	id: string; // UUID serialized as string
	name: string;
	botanical_group: {
		id: string; // UUID serialized as string
		name: string;
		recommended_rotation_years: number | null;
	};
	pests?: Array<{
		id: string; // UUID serialized as string
		name: string;
		treatments?: Array<{ id: string; name: string }>; // UUID serialized as string
		preventions?: Array<{ id: string; name: string }>; // UUID serialized as string
	}>;
	diseases?: Array<{
		id: string; // UUID serialized as string
		name: string;
		symptoms?: Array<{ id: string; name: string }>; // UUID serialized as string
		treatments?: Array<{ id: string; name: string }>; // UUID serialized as string
		preventions?: Array<{ id: string; name: string }>; // UUID serialized as string
	}>;
	antagonises?: Array<{ id: string; name: string }>; // UUID serialized as string
	companion_to?: Array<{ id: string; name: string }>; // UUID serialized as string
}

export async function getBotanicalGroups(
	signal?: AbortSignal,
): Promise<IBotanicalGroup[]> {
	try {
		const response = await api.get<IBotanicalGroup[]>(
			"/families/botanical-groups/",
			{ signal },
		);

		// Handle null or malformed response
		if (!Array.isArray(response.data)) {
			return [];
		}

		return response.data.map((group) => ({
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
		const response = await api.get<IFamilyInfo>(`/families/${familyId}/info`, {
			signal,
		});
		return response.data;
	} catch (error: unknown) {
		if (axios.isCancel(error)) throw error;
		return handleApiError(error, FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR);
	}
}
