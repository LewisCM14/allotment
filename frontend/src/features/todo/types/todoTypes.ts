/**
 * TypeScript types for Weekly Todo feature
 * Matches the Python schema definitions from backend
 */

export interface VarietyTaskDetail {
	variety_id: string;
	variety_name: string;
	family_name: string;
}

export interface FeedTaskDetail {
	feed_id: string;
	feed_name: string;
	varieties: VarietyTaskDetail[];
}

export interface DailyTasks {
	day_id: string;
	day_number: number;
	day_name: string;
	feed_tasks: FeedTaskDetail[];
	water_tasks: VarietyTaskDetail[];
}

export interface WeeklyTasks {
	sow_tasks: VarietyTaskDetail[];
	transplant_tasks: VarietyTaskDetail[];
	harvest_tasks: VarietyTaskDetail[];
	prune_tasks: VarietyTaskDetail[];
	compost_tasks: VarietyTaskDetail[];
}

export interface WeeklyTodoRead {
	week_id: string;
	week_number: number;
	week_start_date: string;
	week_end_date: string;
	weekly_tasks: WeeklyTasks;
	daily_tasks: Record<number, DailyTasks>;
}
