import { PageLayout } from "../../../components/layouts/PageLayout";
import { useEffect, useState, useCallback } from "react";
import { useWeeklyTodo } from "../hooks/useWeeklyTodo";
import { WeekSelector } from "../components/WeekSelector";
import { WeeklyTasksPresenter } from "../components/WeeklyTasksPresenter";
import { DailyTasksPresenter } from "../components/DailyTasksPresenter";
import { WelcomeEmptyState } from "../components/WelcomeEmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { GrowGuideForm } from "../../grow_guide/forms/GrowGuideForm";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { growGuideService } from "../../grow_guide/services/growGuideService";
import { growGuideQueryKey } from "../../grow_guide/hooks/useGrowGuide";

export default function TodoPage() {
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

	const handleWeekChange = (weekNumber: number) => {
		setSelectedWeekNumber(weekNumber);
	};

	useEffect(() => {
		void queryClient.prefetchQuery({
			queryKey: ["growGuideOptions"],
			queryFn: growGuideService.getGrowGuideOptions,
		});
	}, [queryClient]);

	const handleVarietyClick = useCallback(
		(varietyId: string) => {
			setSelectedVarietyId(varietyId);
			setMode("edit");
			setIsGuideOpen(true);
			void queryClient
				.ensureQueryData({
					queryKey: growGuideQueryKey(varietyId),
					queryFn: () => growGuideService.getGrowGuide(varietyId),
				})
				.catch((error) => {
					const message =
						error instanceof Error
							? error.message
							: "Failed to load grow guide";
					toast.error(message);
				});
		},
		[queryClient],
	);

	if (isLoading) {
		return (
			<PageLayout>
				<div className="space-y-6">
					<div>
						<Skeleton className="h-10 w-64 mb-2" />
						<Skeleton className="h-6 w-96" />
					</div>
					<Skeleton className="h-24 w-full" />
					<Skeleton className="h-64 w-full" />
				</div>
			</PageLayout>
		);
	}

	if (isError) {
		// Check if it's a 404 error (no active varieties)
		const errorMessage = error instanceof Error ? error.message : "";
		const isNoActiveVarieties =
			errorMessage.includes("Not Found") ||
			errorMessage.includes("404") ||
			errorMessage.includes("no active varieties");

		if (isNoActiveVarieties) {
			return (
				<PageLayout>
					<WelcomeEmptyState />
				</PageLayout>
			);
		}

		// Other errors (network issues, server errors, etc.)
		return (
			<PageLayout>
				<Alert variant="destructive">
					<AlertCircle className="h-4 w-4" />
					<AlertTitle>Error Loading Tasks</AlertTitle>
					<AlertDescription>
						{errorMessage || "Failed to load weekly tasks. Please try again."}
					</AlertDescription>
				</Alert>
			</PageLayout>
		);
	}

	if (!weeklyTodo) {
		// This shouldn't normally happen, but handle it gracefully
		return (
			<PageLayout>
				<WelcomeEmptyState />
			</PageLayout>
		);
	}

	const hasWeeklyTasks =
		weeklyTodo.weekly_tasks.sow_tasks.length > 0 ||
		weeklyTodo.weekly_tasks.transplant_tasks.length > 0 ||
		weeklyTodo.weekly_tasks.harvest_tasks.length > 0 ||
		weeklyTodo.weekly_tasks.prune_tasks.length > 0 ||
		weeklyTodo.weekly_tasks.compost_tasks.length > 0;

	// Daily tasks object can contain entries for all days even if they have no tasks.
	// Consider it "has daily tasks" only if any day has feed or water items.
	const hasDailyTasks = Object.values(weeklyTodo.daily_tasks).some(
		(d) => (d.feed_tasks?.length ?? 0) > 0 || (d.water_tasks?.length ?? 0) > 0,
	);

	// If backend returned an empty daily_tasks map AND no weekly tasks,
	// this indicates the user has no active varieties. Show the friendly empty state.
	const isNoActiveVarieties =
		Object.keys(weeklyTodo.daily_tasks || {}).length === 0 && !hasWeeklyTasks;

	if (isNoActiveVarieties) {
		return (
			<PageLayout>
				<WelcomeEmptyState />
			</PageLayout>
		);
	}

	return (
		<PageLayout>
			<div className="space-y-6">
				{/* Header */}
				<div>
					<h1 className="text-3xl font-bold tracking-tight">Weekly Tasks</h1>
					<p className="text-muted-foreground mt-1">
						Manage your garden activities for the week
					</p>
				</div>

				{/* Week Selector */}
				<WeekSelector
					currentWeekNumber={weeklyTodo.week_number}
					weekStartDate={weeklyTodo.week_start_date}
					weekEndDate={weeklyTodo.week_end_date}
					onWeekChange={handleWeekChange}
				/>

				{/* No Tasks Message */}
				{!hasWeeklyTasks && !hasDailyTasks && (
					<Alert>
						<CheckCircle2 className="h-4 w-4" />
						<AlertTitle>All Caught Up!</AlertTitle>
						<AlertDescription>
							You have no tasks scheduled for this week. Enjoy your break!
						</AlertDescription>
					</Alert>
				)}

				{/* Tasks Sections */}
				{(hasWeeklyTasks || hasDailyTasks) && (
					<div className="space-y-8">
						{/* Weekly Tasks Section */}
						{hasWeeklyTasks && (
							<div>
								<h2 className="text-2xl font-semibold mb-4">Weekly Tasks</h2>
								<WeeklyTasksPresenter
									sowTasks={weeklyTodo.weekly_tasks.sow_tasks}
									transplantTasks={weeklyTodo.weekly_tasks.transplant_tasks}
									harvestTasks={weeklyTodo.weekly_tasks.harvest_tasks}
									pruneTasks={weeklyTodo.weekly_tasks.prune_tasks}
									compostTasks={weeklyTodo.weekly_tasks.compost_tasks}
									onVarietyClick={handleVarietyClick}
								/>
							</div>
						)}

						{/* Daily Tasks Section */}
						{hasDailyTasks && (
							<div>
								<h2 className="text-2xl font-semibold mb-4">Daily Tasks</h2>
								<DailyTasksPresenter
									dailyTasks={weeklyTodo.daily_tasks}
									onVarietyClick={handleVarietyClick}
								/>
							</div>
						)}
					</div>
				)}
			</div>

			{/* Grow Guide Form Modal */}
			<GrowGuideForm
				isOpen={isGuideOpen}
				onClose={() => setIsGuideOpen(false)}
				varietyId={selectedVarietyId ?? undefined}
				mode={mode}
			/>
		</PageLayout>
	);
}
