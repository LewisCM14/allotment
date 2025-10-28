import api, { handleApiError } from "../../../services/api";
import type { WeeklyTodoRead } from "../types/todoTypes";

/**
 * Todo Service
 * Handles API calls for weekly todo lists
 */
class TodoService {
	/**
	 * Get weekly todo list for a specific week
	 * @param weekNumber - The week number (1-52)
	 * @returns Weekly todo data with tasks
	 */
	async getWeeklyTodo(weekNumber?: number): Promise<WeeklyTodoRead> {
		try {
			const params = weekNumber ? { week_number: weekNumber } : {};
			const response = await api.get<WeeklyTodoRead>("/todos/weekly", {
				params,
			});
			return response.data;
		} catch (error) {
			throw handleApiError(error, "Failed to fetch weekly todo list");
		}
	}

	/**
	 * Get the current week's todo list
	 * @returns Weekly todo data for the current week
	 */
	async getCurrentWeekTodo(): Promise<WeeklyTodoRead> {
		return this.getWeeklyTodo();
	}
}

export const todoService = new TodoService();
