import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWeeklyTodo } from "../hooks/useWeeklyTodo";
import { toast } from "sonner";
import { growGuideService } from "../../grow_guide/services/growGuideService";
import { growGuideQueryKey } from "../../grow_guide/hooks/useGrowGuide";
import type { WeeklyTodoRead } from "../types/todoTypes";

export type TodoContainerRenderProps = {
	weeklyTodo: WeeklyTodoRead | undefined;
	isLoading: boolean;
	isError: boolean;
	error: unknown;
	selectedWeekNumber: number | undefined;
	onWeekChange: (weekNumber: number) => void;
	onVarietyClick: (varietyId: string) => void;
	isGuideOpen: boolean;
	closeGuide: () => void;
	selectedVarietyId: string | null;
	mode: "create" | "edit";
};

export type TodoContainerProps = {
	children: (props: TodoContainerRenderProps) => React.ReactNode;
};

export const TodoContainer = ({ children }: TodoContainerProps) => {
	const [selectedWeekNumber, setSelectedWeekNumber] = useState<
		number | undefined
	>(undefined);
	const [isGuideOpen, setIsGuideOpen] = useState(false);
	const [selectedVarietyId, setSelectedVarietyId] = useState<string | null>(
		null,
	);
	const [mode, setMode] = useState<"create" | "edit">("edit");
	const queryClient = useQueryClient();

	const {
		data: weeklyTodo,
		isLoading,
		isError,
		error,
	} = useWeeklyTodo(selectedWeekNumber);

	const onWeekChange = (weekNumber: number) => {
		setSelectedWeekNumber(weekNumber);
	};

	// Prefetch options used by grow guide form
	useEffect(() => {
		void queryClient.prefetchQuery({
			queryKey: ["growGuideOptions"],
			queryFn: growGuideService.getGrowGuideOptions,
		});
	}, [queryClient]);

	const onVarietyClick = useCallback(
		(varietyId: string) => {
			setSelectedVarietyId(varietyId);
			setMode("edit");
			setIsGuideOpen(true);
			void queryClient
				.ensureQueryData({
					queryKey: growGuideQueryKey(varietyId),
					queryFn: () => growGuideService.getGrowGuide(varietyId),
				})
				.catch((err) => {
					const message =
						err instanceof Error ? err.message : "Failed to load grow guide";
					toast.error(message);
				});
		},
		[queryClient],
	);

	const closeGuide = () => setIsGuideOpen(false);

	return (
		<>
			{children({
				weeklyTodo,
				isLoading,
				isError,
				error,
				selectedWeekNumber,
				onWeekChange,
				onVarietyClick,
				isGuideOpen,
				closeGuide,
				selectedVarietyId,
				mode,
			})}
		</>
	);
};
