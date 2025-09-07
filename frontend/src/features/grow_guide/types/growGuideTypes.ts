// Base schemas from backend
export interface FeedRead {
	feed_id: string;
	feed_name: string;
}

export interface DayRead {
	day_id: string;
	day_number: number;
	day_name: string;
}

export interface FrequencyRead {
	frequency_id: string;
	frequency_name: string;
	frequency_days_per_year: number;
}

export interface LifecycleRead {
	lifecycle_id: string;
	lifecycle_name: string;
	productivity_years: number;
}

export interface PlantingConditionsRead {
	planting_condition_id: string;
	planting_condition: string;
}

export interface WeekRead {
	week_id: string;
	week_number: number;
	week_start_date: string;
	week_end_date: string;
	start_month_id: string;
}

export interface MonthRead {
	month_id: string;
	month_number: number;
	month_name: string;
}

export interface FamilyRead {
	family_id: string;
	family_name: string;
	botanical_group_id: string;
}

export interface VarietyWaterDayRead {
	day: DayRead;
}

export interface VarietyWaterDayUpdate {
	day_id: string;
}

// Main variety schemas
export interface VarietyCreate {
	variety_name: string;
	family_id: string;
	lifecycle_id: string;
	
	// Sowing details (both required)
	sow_week_start_id: string;
	sow_week_end_id: string;
	
	// Transplant details (both must be provided together)
	transplant_week_start_id?: string;
	transplant_week_end_id?: string;
	
	planting_conditions_id: string;
	
	// Soil and spacing details
	soil_ph: number;
	row_width_cm?: number;
	plant_depth_cm: number;
	plant_space_cm: number;
	
	// Feed details (all three must be provided together)
	feed_id?: string;
	feed_week_start_id?: string;
	feed_frequency_id?: string;
	
	// Watering details (required)
	water_frequency_id: string;
	
	// High temperature details
	high_temp_degrees?: number;
	high_temp_water_frequency_id?: string;
	
	// Harvest details (both required)
	harvest_week_start_id: string;
	harvest_week_end_id: string;
	
	// Prune details (both must be provided together)
	prune_week_start_id?: string;
	prune_week_end_id?: string;
	
	notes?: string;
	is_public?: boolean;
}

export interface VarietyUpdate {
	variety_name?: string;
	family_id?: string;
	lifecycle_id?: string;
	
	// Sowing details
	sow_week_start_id?: string;
	sow_week_end_id?: string;
	
	// Transplant details
	transplant_week_start_id?: string;
	transplant_week_end_id?: string;
	
	planting_conditions_id?: string;
	
	// Soil and spacing details
	soil_ph?: number;
	row_width_cm?: number;
	plant_depth_cm?: number;
	plant_space_cm?: number;
	
	// Feed details
	feed_id?: string;
	feed_week_start_id?: string;
	feed_frequency_id?: string;
	
	// Watering details
	water_frequency_id?: string;
	
	// High temperature details
	high_temp_degrees?: number;
	high_temp_water_frequency_id?: string;
	
	// Harvest details
	harvest_week_start_id?: string;
	harvest_week_end_id?: string;
	
	// Prune details
	prune_week_start_id?: string;
	prune_week_end_id?: string;
	
	notes?: string;
	is_public?: boolean;
}

export interface VarietyRead {
	variety_id: string;
	variety_name: string;
	owner_user_id: string;
	
	// Related objects
	family: FamilyRead;
	lifecycle: LifecycleRead;
	planting_conditions: PlantingConditionsRead;
	
	// Sowing details (required)
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
	feed?: FeedRead;
	feed_week_start_id?: string;
	feed_frequency?: FrequencyRead;
	
	// Watering details (required)
	water_frequency: FrequencyRead;
	
	// High temperature details
	high_temp_degrees?: number;
	high_temp_water_frequency: FrequencyRead;
	
	// Harvest details (required)
	harvest_week_start_id: string;
	harvest_week_end_id: string;
	
	// Prune details
	prune_week_start_id?: string;
	prune_week_end_id?: string;
	
	notes?: string;
	is_public: boolean;
	last_updated: string;
	
	// Water days
	water_days: VarietyWaterDayRead[];
}

export interface VarietyListRead {
	variety_id: string;
	variety_name: string;
	lifecycle: LifecycleRead;
	is_public: boolean;
	last_updated: string;
}

export interface VarietyOptionsRead {
	lifecycles: LifecycleRead[];
	planting_conditions: PlantingConditionsRead[];
	frequencies: FrequencyRead[];
	feeds: FeedRead[];
	weeks: WeekRead[];
	families: FamilyRead[];
}
