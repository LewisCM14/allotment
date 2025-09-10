// Shared Grow Guide (Variety) Types used by service tests

export interface VarietyCreate {
	variety_name: string;
	family_id: string;
	lifecycle_id: string;
	sow_week_start_id: string;
	sow_week_end_id: string;
	planting_conditions_id: string;
	soil_ph: number;
	plant_depth_cm: number;
	plant_space_cm: number;
	water_frequency_id: string;
	harvest_week_start_id: string;
	harvest_week_end_id: string;
	// Optional fields
	transplant_week_start_id?: string;
	transplant_week_end_id?: string;
	feed_id?: string;
	feed_week_start_id?: string;
	feed_frequency_id?: string;
	high_temp_degrees?: number;
	high_temp_water_frequency_id?: string;
	prune_week_start_id?: string;
	prune_week_end_id?: string;
	notes?: string;
	is_public?: boolean;
	water_days?: { day_id: string }[];
}

export interface VarietyUpdate {
	variety_name?: string;
	soil_ph?: number;
	plant_depth_cm?: number;
	plant_space_cm?: number;
	feed_id?: string | null;
	feed_week_start_id?: string | null;
	feed_frequency_id?: string | null;
	high_temp_degrees?: number | null;
	high_temp_water_frequency_id?: string | null;
	prune_week_start_id?: string | null;
	prune_week_end_id?: string | null;
	notes?: string | null;
	is_public?: boolean;
	water_days?: { day_id: string }[];
}

export interface LifecycleRead {
	lifecycle_id: string;
	lifecycle_name: string;
	productivity_years: number;
}

export interface PlantingConditionRead {
	planting_condition_id: string;
	planting_condition: string;
}

export interface FrequencyRead {
	frequency_id: string;
	frequency_name: string;
	frequency_days_per_year: number;
}

export interface FeedRead {
	feed_id: string;
	feed_name: string;
}

export interface WeekRead {
	week_id: string;
	week_number: number;
	week_start_date: string;
	week_end_date: string;
	// Some tests reference these optional fields
	start_month_id?: string;
	end_month_id?: string;
}

export interface FamilyRead {
	family_id: string;
	family_name: string;
	botanical_group_id?: string;
}

export interface DayRead {
	day_id: string;
	day_number: number;
	day_name: string;
}

export interface VarietyOptionsRead {
	lifecycles: LifecycleRead[];
	planting_conditions: PlantingConditionRead[];
	frequencies: FrequencyRead[];
	feeds: FeedRead[];
	weeks: WeekRead[];
	families: FamilyRead[];
	days?: DayRead[];
}

export interface VarietyListRead {
	variety_id: string;
	variety_name: string;
	lifecycle: LifecycleRead;
	is_public: boolean;
	last_updated: string;
}

export interface VarietyRead extends VarietyListRead {
	owner_user_id: string;
	family: FamilyRead;
	planting_conditions: PlantingConditionRead;
	sow_week_start_id: string;
	sow_week_end_id: string;
	transplant_week_start_id?: string;
	transplant_week_end_id?: string;
	soil_ph: number;
	row_width_cm?: number;
	plant_depth_cm: number;
	plant_space_cm: number;
	feed?: FeedRead;
	feed_week_start_id?: string;
	feed_frequency?: FrequencyRead;
	water_frequency: FrequencyRead;
	high_temp_degrees?: number;
	high_temp_water_frequency?: FrequencyRead;
	harvest_week_start_id: string;
	harvest_week_end_id: string;
	prune_week_start_id?: string;
	prune_week_end_id?: string;
	notes?: string;
	water_days: { day: DayRead }[];
}
