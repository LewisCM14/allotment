import api, { handleApiError } from "../../../services/api";
import { errorMonitor } from "../../../services/errorMonitoring";
import type { GrowGuideFormData } from "../forms/GrowGuideFormSchema";
import type { VarietyCreate } from "../types/growGuideTypes";

export interface Lifecycle {
	lifecycle_id: string;
	lifecycle_name: string;
	productivity_years: number;
}

export interface VarietyList {
	variety_id: string;
	variety_name: string;
	family: { family_id: string; family_name: string };
	lifecycle: Lifecycle;
	is_public: boolean;
	last_updated: string;
}

export interface GrowGuideOptions {
	lifecycles: {
		lifecycle_id: string;
		lifecycle_name: string;
		productivity_years: number;
	}[];
	planting_conditions: {
		planting_condition_id: string;
		planting_condition: string;
	}[];
	frequencies: {
		frequency_id: string;
		frequency_name: string;
		frequency_days_per_year: number;
	}[];
	feed_frequencies: {
		frequency_id: string;
		frequency_name: string;
		frequency_days_per_year: number;
	}[];
	feeds: { feed_id: string; feed_name: string }[];
	weeks: {
		week_id: string;
		week_number: number;
		week_start_date: string;
		week_end_date: string;
	}[];
	families: { family_id: string; family_name: string }[];
	days?: { day_id: string; day_number: number; day_name: string }[];
}

export interface GrowGuideDetail extends VarietyList {
	variety_id: string;
	variety_name: string;
	owner_user_id: string;
	family: { family_id: string; family_name: string };
	lifecycle: {
		lifecycle_id: string;
		lifecycle_name: string;
		productivity_years: number;
	};
	planting_conditions: {
		planting_condition_id: string;
		planting_condition: string;
	};

	// Sowing details
	sow_week_start_id: string;
	sow_week_end_id: string;

	// Transplant details
	transplant_week_start_id?: string;
	transplant_week_end_id?: string;

	// Soil and spacing details
	soil_ph: number;
	row_width_cm?: number;
	plant_depth_cm: number;
	plant_space_cm: number;

	// Feed details
	feed?: { feed_id: string; feed_name: string };
	feed_week_start_id?: string;
	feed_frequency?: {
		frequency_id: string;
		frequency_name: string;
		frequency_days_per_year: number;
	};

	// Watering details
	water_frequency: {
		frequency_id: string;
		frequency_name: string;
		frequency_days_per_year: number;
	};

	// High temperature details
	high_temp_degrees?: number;
	high_temp_water_frequency?: {
		frequency_id: string;
		frequency_name: string;
		frequency_days_per_year: number;
	};

	// Harvest details
	harvest_week_start_id: string;
	harvest_week_end_id: string;

	// Prune details
	prune_week_start_id?: string;
	prune_week_end_id?: string;

	notes?: string;
	is_public: boolean;
	last_updated: string;

	// Water days
	water_days: {
		day: { day_id: string; day_number: number; day_name: string };
	}[];
}

const getUserGrowGuides = async (): Promise<VarietyList[]> => {
	try {
		const response = await api.get<VarietyList[]>("/grow-guides", {
			params: { visibility: "user" },
		});
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getUserGrowGuides",
			url: "/grow-guides?visibility=user",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch user grow guides. Please try again.",
		);
	}
};

const getPublicGrowGuides = async (): Promise<VarietyList[]> => {
	try {
		const response = await api.get<VarietyList[]>("/grow-guides", {
			params: { visibility: "public" },
		});
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getPublicGrowGuides",
			url: "/grow-guides?visibility=public",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch public grow guides. Please try again.",
		);
	}
};

const createGrowGuide = async (
	data: VarietyCreate | GrowGuideFormData,
): Promise<GrowGuideDetail> => {
	const { is_public, ...rest } = data as VarietyCreate;
	const payload: VarietyCreate = {
		...rest,
		is_public: is_public ?? false,
	};
	try {
		const response = await api.post<GrowGuideDetail>("/grow-guides", payload);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "createGrowGuide",
			url: "/grow-guides",
			method: "POST",
			data: payload,
		});
		return handleApiError(
			error,
			"Failed to create grow guide. Please try again.",
		);
	}
};

const getGrowGuideOptions = async (): Promise<GrowGuideOptions> => {
	try {
		const response = await api.get<GrowGuideOptions>("/grow-guides/metadata");
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getGrowGuideOptions",
			url: "/grow-guides/metadata",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch grow guide options. Please try again.",
		);
	}
};

const getGrowGuide = async (varietyId: string): Promise<GrowGuideDetail> => {
	try {
		const response = await api.get<GrowGuideDetail>(
			`/grow-guides/${varietyId}`,
		);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getGrowGuide",
			url: `/grow-guides/${varietyId}`,
			method: "GET",
		});
		return handleApiError(error, "Failed to fetch grow guide details.");
	}
};

// Extra CRUD helpers expected by existing tests (legacy naming retained for now)
const updateVariety = async (
	varietyId: string,
	data: Partial<GrowGuideFormData>,
): Promise<GrowGuideDetail> => {
	try {
		const response = await api.put<GrowGuideDetail>(
			`/grow-guides/${varietyId}`,
			data,
		);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "updateVariety",
			url: `/grow-guides/${varietyId}`,
			method: "PUT",
			data,
		});
		return handleApiError(error, "Failed to update grow guide.");
	}
};

const deleteVariety = async (varietyId: string): Promise<void> => {
	try {
		await api.delete(`/grow-guides/${varietyId}`);
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "deleteVariety",
			url: `/grow-guides/${varietyId}`,
			method: "DELETE",
		});
		return handleApiError(error, "Failed to delete grow guide.");
	}
};

const toggleVarietyPublic = async (
	varietyId: string,
	currentIsPublic: boolean,
): Promise<GrowGuideDetail> => {
	const payload = { is_public: !currentIsPublic };
	try {
		const response = await api.put<GrowGuideDetail>(
			`/grow-guides/${varietyId}`,
			payload,
		);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "toggleVarietyPublic",
			url: `/grow-guides/${varietyId}`,
			method: "PUT",
			data: payload,
		});
		return handleApiError(error, "Failed to toggle public status.");
	}
};

const copyPublicVariety = async (
	publicVarietyId: string,
): Promise<GrowGuideDetail> => {
	try {
		// Assuming backend supports copy endpoint; adjust when implemented
		const response = await api.post<GrowGuideDetail>(
			`/grow-guides/${publicVarietyId}/copy`,
			{},
		);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "copyPublicVariety",
			url: `/grow-guides/${publicVarietyId}/copy`,
			method: "POST",
		});
		return handleApiError(error, "Failed to copy public grow guide.");
	}
};

export const growGuideService = {
	getUserGrowGuides,
	getPublicGrowGuides,
	createGrowGuide,
	getGrowGuideOptions,
	getGrowGuide,
	updateVariety,
	deleteVariety,
	toggleVarietyPublic,
	copyPublicVariety,
};
