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
		// Keep todo data fresh for 5 minutes
		staleTime: 5 * 60 * 1000,
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
