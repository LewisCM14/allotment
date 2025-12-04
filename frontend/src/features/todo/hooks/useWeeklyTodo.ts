import { useQuery } from "@tanstack/react-query";
import { todoService } from "../services/todoService";

/**
 * Hook to fetch weekly todo data
 * @param weekNumber - Optional week number (1-52). If not provided, fetches current week.
 * @returns React Query result with weekly todo data
 */
export const useWeeklyTodo = (weekNumber?: number) => {
	return useQuery({
		queryKey: ["weeklyTodo", weekNumber],
		queryFn: () => todoService.getWeeklyTodo(weekNumber),
		staleTime: 24 * 60 * 60 * 1000, // 24 hours
		gcTime: 24 * 60 * 60 * 1000, // 24 hours
		// Refetch when window regains focus
		refetchOnWindowFocus: true,
	});
};

/**
 * Query key factory for weekly todo queries
 * Useful for invalidating or prefetching specific weeks
 */
export const weeklyTodoQueryKey = (weekNumber?: number) => [
	"weeklyTodo",
	weekNumber,
];
