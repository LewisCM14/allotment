import { PageLayout } from "../../../components/layouts/PageLayout";
import { WeekSelector } from "../components/WeekSelector";
import { WeeklyTasksPresenter } from "../components/WeeklyTasksPresenter";
import { DailyTasksPresenter } from "../components/DailyTasksPresenter";
import { WelcomeEmptyState } from "../components/WelcomeEmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { GrowGuideForm } from "../../grow_guide/forms/GrowGuideForm";
import { AppError } from "@/services/api";
import { TodoContainer } from "../components/TodoContainer";

export default function TodoPage() {
	return (
		<TodoContainer>
			{({
				weeklyTodo,
				isLoading,
				isError,
				error,
				onWeekChange,
				onVarietyClick,
				isGuideOpen,
				closeGuide,
				selectedVarietyId,
				mode,
			}) => {
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
					const errorMessage = error instanceof Error ? error.message : "";
					const statusCode =
						error instanceof AppError ? error.statusCode : undefined;
					const isNoActiveVarieties =
						statusCode === 404 || errorMessage.includes("no active varieties");

					if (isNoActiveVarieties) {
						return (
							<PageLayout>
								<WelcomeEmptyState />
							</PageLayout>
						);
					}

					return (
						<PageLayout>
							<Alert variant="destructive">
								<AlertCircle className="h-4 w-4" />
								<AlertTitle>Error Loading Tasks</AlertTitle>
								<AlertDescription>
									{errorMessage ||
										"Failed to load weekly tasks. Please try again."}
								</AlertDescription>
							</Alert>
						</PageLayout>
					);
				}

				if (!weeklyTodo) {
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

				const hasDailyTasks = Object.values(weeklyTodo.daily_tasks).some(
					(d) =>
						(d.feed_tasks?.length ?? 0) > 0 || (d.water_tasks?.length ?? 0) > 0,
				);

				const isNoActiveVarieties =
					Object.keys(weeklyTodo.daily_tasks || {}).length === 0 &&
					!hasWeeklyTasks;

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
							<div>
								<h1 className="text-3xl font-bold tracking-tight">
									Weekly Tasks
								</h1>
								<p className="text-muted-foreground mt-1">
									Manage your garden activities for the week
								</p>
							</div>

							<WeekSelector
								currentWeekNumber={weeklyTodo.week_number}
								weekStartDate={weeklyTodo.week_start_date}
								weekEndDate={weeklyTodo.week_end_date}
								onWeekChange={onWeekChange}
							/>

							{!hasWeeklyTasks && !hasDailyTasks && (
								<Alert>
									<CheckCircle2 className="h-4 w-4" />
									<AlertTitle>All Caught Up!</AlertTitle>
									<AlertDescription>
										You have no tasks scheduled for this week. Enjoy your break!
									</AlertDescription>
								</Alert>
							)}

							{(hasWeeklyTasks || hasDailyTasks) && (
								<div className="space-y-8">
									{hasWeeklyTasks && (
										<div>
											<h2 className="text-2xl font-semibold mb-4">
												Weekly Tasks
											</h2>
											<WeeklyTasksPresenter
												sowTasks={weeklyTodo.weekly_tasks.sow_tasks}
												transplantTasks={
													weeklyTodo.weekly_tasks.transplant_tasks
												}
												harvestTasks={weeklyTodo.weekly_tasks.harvest_tasks}
												pruneTasks={weeklyTodo.weekly_tasks.prune_tasks}
												compostTasks={weeklyTodo.weekly_tasks.compost_tasks}
												onVarietyClick={onVarietyClick}
											/>
										</div>
									)}

									{hasDailyTasks && (
										<div>
											<h2 className="text-2xl font-semibold mb-4">
												Daily Tasks
											</h2>
											<DailyTasksPresenter
												dailyTasks={weeklyTodo.daily_tasks}
												onVarietyClick={onVarietyClick}
											/>
										</div>
									)}
								</div>
							)}
						</div>

						<GrowGuideForm
							isOpen={isGuideOpen}
							onClose={closeGuide}
							varietyId={selectedVarietyId ?? undefined}
							mode={mode}
						/>
					</PageLayout>
				);
			}}
		</TodoContainer>
	);
}
