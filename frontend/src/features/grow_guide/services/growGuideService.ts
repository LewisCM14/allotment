import api, { handleApiError } from "../../../services/api";
import { errorMonitor } from "../../../services/errorMonitoring";
import type { GrowGuideFormData } from "../forms/GrowGuideFormSchema";

export interface Lifecycle {
	lifecycle_id: string;
	lifecycle_name: string;
	productivity_years: number;
}

export interface VarietyList {
	variety_id: string;
	variety_name: string;
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
		const response = await api.get<VarietyList[]>("/grow-guides");
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getUserGrowGuides",
			url: "/grow-guides",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch user grow guides. Please try again.",
		);
	}
};

const createGrowGuide = async (
	data: GrowGuideFormData,
): Promise<GrowGuideDetail> => {
	try {
		const response = await api.post<GrowGuideDetail>("/grow-guides", data);
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "createGrowGuide",
			url: "/grow-guides",
			method: "POST",
			data,
		});
		return handleApiError(
			error,
			"Failed to create grow guide. Please try again.",
		);
	}
};

const getGrowGuideOptions = async (): Promise<GrowGuideOptions> => {
	try {
		const response = await api.get<GrowGuideOptions>("/grow-guides/options");
		return response.data;
	} catch (error: unknown) {
		errorMonitor.captureException(error, {
			context: "getGrowGuideOptions",
			url: "/grow-guides/options",
			method: "GET",
		});
		return handleApiError(
			error,
			"Failed to fetch grow guide options. Please try again.",
		);
	}
};

export const growGuideService = {
	getUserGrowGuides,
	createGrowGuide,
	getGrowGuideOptions,
};
