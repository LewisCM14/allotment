import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { DailyTasks } from "../types/todoTypes";
import { Droplets, Leaf } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface DailyTasksPresenterProps {
	dailyTasks: Record<number, DailyTasks>;
}

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export const DailyTasksPresenter = ({
	dailyTasks,
}: DailyTasksPresenterProps) => {
	// Convert dailyTasks object to sorted array
	const sortedDays = Object.values(dailyTasks).sort(
		(a, b) => a.day_number - b.day_number,
	);

	if (sortedDays.length === 0) {
		return (
			<Card>
				<CardContent className="pt-6">
					<p className="text-center text-muted-foreground">
						No daily tasks scheduled for this week.
					</p>
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="space-y-4">
			{sortedDays.map((day) => {
				const hasFeedTasks = day.feed_tasks.length > 0;
				const hasWaterTasks = day.water_tasks.length > 0;

				if (!hasFeedTasks && !hasWaterTasks) {
					return null;
				}

				return (
					<Card key={day.day_id}>
						<CardHeader className="pb-3">
							<div className="flex items-center justify-between">
								<CardTitle className="text-lg">
									{DAY_NAMES[day.day_number - 1]} - {day.day_name}
								</CardTitle>
								<div className="flex gap-2">
									{hasFeedTasks && (
										<Badge variant="outline" className="bg-green-50">
											<Leaf className="h-3 w-3 mr-1" />
											{day.feed_tasks.reduce(
												(sum, feed) => sum + feed.varieties.length,
												0,
											)}{" "}
											Feed
										</Badge>
									)}
									{hasWaterTasks && (
										<Badge variant="outline" className="bg-blue-50">
											<Droplets className="h-3 w-3 mr-1" />
											{day.water_tasks.length} Water
										</Badge>
									)}
								</div>
							</div>
						</CardHeader>
						<CardContent className="space-y-4">
							{/* Feed Tasks */}
							{hasFeedTasks && (
								<div>
									<div className="flex items-center gap-2 mb-3">
										<Leaf className="h-4 w-4 text-green-600" />
										<h4 className="font-semibold text-sm">Feeding</h4>
									</div>
									<div className="space-y-3">
										{day.feed_tasks.map((feedTask) => (
											<div
												key={feedTask.feed_id}
												className="p-3 bg-green-50 dark:bg-green-950/20 rounded-md border border-green-200 dark:border-green-900"
											>
												<div className="flex items-center justify-between mb-2">
													<span className="font-medium text-green-800 dark:text-green-200">
														{feedTask.feed_name}
													</span>
													<Badge
														variant="secondary"
														className="bg-green-100 dark:bg-green-900"
													>
														{feedTask.varieties.length}{" "}
														{feedTask.varieties.length === 1
															? "variety"
															: "varieties"}
													</Badge>
												</div>
												<div className="space-y-1">
													{feedTask.varieties.map((variety) => (
														<div
															key={variety.variety_id}
															className="flex items-center justify-between text-sm p-2 bg-white dark:bg-gray-900 rounded"
														>
															<span>{variety.variety_name}</span>
															<span className="text-muted-foreground text-xs">
																{variety.family_name}
															</span>
														</div>
													))}
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* Separator if both tasks exist */}
							{hasFeedTasks && hasWaterTasks && (
								<div className="border-t border-gray-200 dark:border-gray-800" />
							)}

							{/* Water Tasks */}
							{hasWaterTasks && (
								<div>
									<div className="flex items-center gap-2 mb-3">
										<Droplets className="h-4 w-4 text-blue-600" />
										<h4 className="font-semibold text-sm">Watering</h4>
									</div>
									<div className="space-y-2">
										{day.water_tasks.map((variety) => (
											<div
												key={variety.variety_id}
												className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 rounded-md border border-blue-200 dark:border-blue-900"
											>
												<span className="font-medium text-blue-800 dark:text-blue-200">
													{variety.variety_name}
												</span>
												<span className="text-sm text-muted-foreground">
													{variety.family_name}
												</span>
											</div>
										))}
									</div>
								</div>
							)}
						</CardContent>
					</Card>
				);
			})}
		</div>
	);
};
