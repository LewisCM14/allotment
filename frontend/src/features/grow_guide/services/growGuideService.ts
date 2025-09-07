import api, { handleApiError } from "../../../services/api";
import type {
	VarietyCreate,
	VarietyListRead,
	VarietyOptionsRead,
	VarietyRead,
	VarietyUpdate,
} from "../types/growGuideTypes";

// Get all available options for variety creation/editing
export const getVarietyOptions = async (): Promise<VarietyOptionsRead> => {
	try {
		const response = await api.get<VarietyOptionsRead>("/grow_guide/options");
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to load variety options. Please try again.");
	}
};

// Get user's varieties
export const getUserVarieties = async (): Promise<VarietyListRead[]> => {
	try {
		const response = await api.get<VarietyListRead[]>("/grow_guide");
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to load your varieties. Please try again.");
	}
};

// Get a specific variety by ID
export const getVariety = async (varietyId: string): Promise<VarietyRead> => {
	try {
		const response = await api.get<VarietyRead>(`/grow_guide/${varietyId}`);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to load variety details. Please try again.");
	}
};

// Get user's specific variety
export const getUserVariety = async (varietyId: string): Promise<VarietyRead> => {
	try {
		const response = await api.get<VarietyRead>(`/grow_guide/user/${varietyId}`);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to load variety details. Please try again.");
	}
};

// Create new variety
export const createVariety = async (varietyData: VarietyCreate): Promise<VarietyRead> => {
	try {
		const response = await api.post<VarietyRead>("/grow_guide", varietyData);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to create variety. Please try again.");
	}
};

// Update existing variety
export const updateVariety = async (
	varietyId: string,
	varietyData: VarietyUpdate,
): Promise<VarietyRead> => {
	try {
		const response = await api.put<VarietyRead>(`/grow_guide/${varietyId}`, varietyData);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to update variety. Please try again.");
	}
};

// Delete variety
export const deleteVariety = async (varietyId: string): Promise<void> => {
	try {
		await api.delete(`/grow_guide/${varietyId}`);
	} catch (error: unknown) {
		return handleApiError(error, "Failed to delete variety. Please try again.");
	}
};

// Set watering days for variety
export const setVarietyWaterDays = async (
	varietyId: string,
	waterDays: string[],
): Promise<VarietyRead> => {
	try {
		const response = await api.put<VarietyRead>(`/grow_guide/${varietyId}/water-days`, {
			water_days: waterDays,
		});
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to update watering schedule. Please try again.");
	}
};

// Get public varieties (for copying)
export const getPublicVarieties = async (): Promise<VarietyListRead[]> => {
	try {
		const response = await api.get<VarietyListRead[]>("/grow_guide/public");
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to load public varieties. Please try again.");
	}
};

// Copy public variety to user's collection
export const copyPublicVariety = async (varietyId: string): Promise<VarietyRead> => {
	try {
		const response = await api.post<VarietyRead>(`/grow_guide/copy/${varietyId}`);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to copy variety. Please try again.");
	}
};

// Toggle variety public status
export const toggleVarietyPublic = async (varietyId: string): Promise<VarietyRead> => {
	try {
		const response = await api.patch<VarietyRead>(`/grow_guide/${varietyId}/toggle-public`);
		return response.data;
	} catch (error: unknown) {
		return handleApiError(error, "Failed to update variety visibility. Please try again.");
	}
};
