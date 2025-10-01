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
	family_id: string;
	family_name: string;
}

export interface IBotanicalGroup {
	botanical_group_id: string;
	botanical_group_name: string;
	rotate_years: number | null;
	families: IFamily[];
}

export interface IInterventionRef {
	intervention_id: string;
	intervention_name: string;
}

export interface IPest {
	pest_id: string;
	pest_name: string;
	treatments?: IInterventionRef[];
	preventions?: IInterventionRef[];
}

export interface ISymptom {
	symptom_id: string;
	symptom_name: string;
}

export interface IDisease {
	disease_id: string;
	disease_name: string;
	symptoms?: ISymptom[];
	treatments?: IInterventionRef[];
	preventions?: IInterventionRef[];
}

export interface IFamilyRelation {
	family_id: string;
	family_name: string;
}

export interface IBotanicalGroupInfo {
	botanical_group_id: string;
	botanical_group_name: string;
	rotate_years: number | null;
}

export interface IFamilyInfo {
	family_id: string;
	family_name: string;
	botanical_group: IBotanicalGroupInfo;
	pests?: IPest[];
	diseases?: IDisease[];
	antagonises?: IFamilyRelation[];
	companion_to?: IFamilyRelation[];
}

export async function getBotanicalGroups(
	signal?: AbortSignal,
): Promise<IBotanicalGroup[]> {
	try {
		const response = await api.get<IBotanicalGroup[]>(
			"/families/botanical-groups/",
			{ signal },
		);
		return Array.isArray(response.data) ? response.data : [];
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
