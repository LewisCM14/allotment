import api, { handleApiError } from "@/services/api";
import { formatError } from "@/utils/errorUtils";
import axios from "axios";

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

export async function getBotanicalGroups(
	signal?: AbortSignal,
): Promise<IBotanicalGroup[]> {
	try {
		const response = await api.get<IBotanicalGroup[]>(
			`${API_PREFIX}/families/botanical-groups/`,
			{
				signal,
			},
		);
		return response.data;
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
		handleApiError(error, FAMILY_SERVICE_ERRORS.FETCH_BOTANICAL_GROUPS_FAILED);
		throw new Error(FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR);
	}
}
