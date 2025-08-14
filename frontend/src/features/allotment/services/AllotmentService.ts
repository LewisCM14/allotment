import api, { handleApiError } from "../../../services/api";
import axios from "axios";

export class NoAllotmentFoundError extends Error {
	constructor(message = "No allotment found") {
		super(message);
		this.name = "NoAllotmentFoundError";
	}
}

export interface IAllotmentRequest {
	allotment_postal_zip_code: string;
	allotment_width_meters: number;
	allotment_length_meters: number;
}

export interface IAllotmentUpdateRequest {
	allotment_postal_zip_code?: string;
	allotment_width_meters?: number;
	allotment_length_meters?: number;
}

export interface IAllotmentResponse {
	user_allotment_id: string; // UUID as string from backend
	user_id: string; // UUID as string from backend
	allotment_postal_zip_code: string;
	allotment_width_meters: number; // Compatible with backend float
	allotment_length_meters: number; // Compatible with backend float
}

export const createUserAllotment = async (
	allotmentData: IAllotmentRequest,
): Promise<IAllotmentResponse> => {
	try {
		const response = await api.post<IAllotmentResponse>(
			"/users/allotment",
			allotmentData,
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(
			error,
			"Failed to create allotment. Please try again.",
		);
	}
};

export const getUserAllotment = async (): Promise<IAllotmentResponse> => {
	try {
		// Use regular GET instead of cached GET since React Query handles caching
		const response = await api.get<IAllotmentResponse>("/users/allotment");
		return response.data;
	} catch (error: unknown) {
		if (axios.isAxiosError(error)) {
			if (!error.response) {
				return handleApiError(
					error,
					"Failed to fetch allotment. Please try again.",
				);
			}

			if (error.response.status === 404) {
				throw new NoAllotmentFoundError("No allotment found for this user");
			}
		}

		return handleApiError(
			error,
			"Failed to fetch allotment. Please try again.",
		);
	}
};

export const updateUserAllotment = async (
	allotmentData: IAllotmentUpdateRequest,
): Promise<IAllotmentResponse> => {
	try {
		const response = await api.put<IAllotmentResponse>(
			"/users/allotment",
			allotmentData,
		);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(
			error,
			"Failed to update allotment. Please try again.",
		);
	}
};
