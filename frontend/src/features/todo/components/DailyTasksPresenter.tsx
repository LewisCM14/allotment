import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { DailyTasks } from "../types/todoTypes";
import { Droplets, Leaf } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface DailyTasksPresenterProps {
	readonly dailyTasks: Record<number, DailyTasks>;
	readonly onVarietyClick?: (varietyId: string) => void;
}

const FULL_DAY_NAMES = [
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
];

type FeedTask = DailyTasks["feed_tasks"][number];
type WaterVariety = DailyTasks["water_tasks"][number];

type FeedVarietyButtonProps = Readonly<{
	variety: FeedTask["varieties"][number];
	onVarietyClick?: (varietyId: string) => void;
}>;

function FeedVarietyButton({
	variety,
	onVarietyClick,
}: FeedVarietyButtonProps) {
	const handleClick = () => onVarietyClick?.(variety.variety_id);
	return (
		<button
			key={variety.variety_id}
			type="button"
			onClick={handleClick}
			className="w-full flex items-center justify-between text-sm p-2 rounded border bg-primary/10 text-foreground border-primary/40 hover:bg-primary/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background cursor-pointer"
		>
			<span className="text-foreground">{variety.variety_name}</span>
			<span className="text-muted-foreground text-xs">
				{variety.family_name}
			</span>
		</button>
	);
}

type FeedTaskCardProps = Readonly<{
	feedTask: FeedTask;
	onVarietyClick?: (varietyId: string) => void;
}>;

function FeedTaskCard({ feedTask, onVarietyClick }: FeedTaskCardProps) {
	return (
		<div
			key={feedTask.feed_id}
			className="p-3 rounded-md border bg-primary/10 border-primary/40"
		>
			<div className="flex items-center justify-between mb-2">
				<span className="font-medium text-green-800 dark:text-green-200">
					{feedTask.feed_name}
				</span>
				<Badge
					variant="secondary"
					className="bg-primary/20 text-foreground border border-primary/40"
				>
					{feedTask.varieties.length}{" "}
					{feedTask.varieties.length === 1 ? "variety" : "varieties"}
				</Badge>
			</div>
			<div className="space-y-1">
				{feedTask.varieties.map((variety) => (
					<FeedVarietyButton
						key={variety.variety_id}
						variety={variety}
						onVarietyClick={onVarietyClick}
					/>
				))}
			</div>
		</div>
	);
}

type FeedSectionProps = Readonly<{
	feedTasks: DailyTasks["feed_tasks"];
	onVarietyClick?: (varietyId: string) => void;
}>;

function FeedSection({ feedTasks, onVarietyClick }: FeedSectionProps) {
	return (
		<div>
			<div className="flex items-center gap-2 mb-3">
				<Leaf className="h-4 w-4 text-green-600" />
				<h4 className="font-semibold text-sm">Feeding</h4>
			</div>
			<div className="space-y-3">
				{feedTasks.map((feedTask) => (
					<FeedTaskCard
						key={feedTask.feed_id}
						feedTask={feedTask}
						onVarietyClick={onVarietyClick}
					/>
				))}
			</div>
		</div>
	);
}

type WaterTaskButtonProps = Readonly<{
	variety: WaterVariety;
	onVarietyClick?: (varietyId: string) => void;
}>;

function WaterTaskButton({ variety, onVarietyClick }: WaterTaskButtonProps) {
	const handleClick = () => onVarietyClick?.(variety.variety_id);
	return (
		<button
			key={variety.variety_id}
			type="button"
			onClick={handleClick}
			className="w-full text-left flex items-center justify-between p-3 rounded-md border bg-accent/15 text-foreground border-accent/40 hover:bg-accent/25 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background cursor-pointer"
		>
			<span className="font-medium text-foreground">
				{variety.variety_name}
			</span>
			<span className="text-sm text-muted-foreground">
				{variety.family_name}
			</span>
		</button>
	);
}

type WaterSectionProps = Readonly<{
	waterTasks: DailyTasks["water_tasks"];
	onVarietyClick?: (varietyId: string) => void;
}>;

function WaterSection({ waterTasks, onVarietyClick }: WaterSectionProps) {
	return (
		<div>
			<div className="flex items-center gap-2 mb-3">
				<Droplets className="h-4 w-4 text-blue-600" />
				<h4 className="font-semibold text-sm">Watering</h4>
			</div>
			<div className="space-y-2">
				{waterTasks.map((variety) => (
					<WaterTaskButton
						key={variety.variety_id}
						variety={variety}
						onVarietyClick={onVarietyClick}
					/>
				))}
			</div>
		</div>
	);
}

function getTotalFeedVarieties(feedTasks: DailyTasks["feed_tasks"]) {
	return feedTasks.reduce((sum, feed) => sum + feed.varieties.length, 0);
}

export const DailyTasksPresenter = ({
	dailyTasks,
	onVarietyClick,
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
									{FULL_DAY_NAMES[day.day_number - 1]}
								</CardTitle>
								<div className="flex gap-2">
									{hasFeedTasks && (
										<Badge
											variant="outline"
											className="bg-primary/20 text-foreground border-primary/40"
										>
											<Leaf className="h-3 w-3 mr-1" />
											{getTotalFeedVarieties(day.feed_tasks)} Feed
										</Badge>
									)}
									{hasWaterTasks && (
										<Badge
											variant="outline"
											className="bg-accent/20 text-foreground border-accent/40"
										>
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
								<FeedSection
									feedTasks={day.feed_tasks}
									onVarietyClick={onVarietyClick}
								/>
							)}

							{/* Separator if both tasks exist */}
							{hasFeedTasks && hasWaterTasks && (
								<div className="border-t border-gray-200 dark:border-gray-800" />
							)}

							{/* Water Tasks */}
							{hasWaterTasks && (
								<WaterSection
									waterTasks={day.water_tasks}
									onVarietyClick={onVarietyClick}
								/>
							)}
						</CardContent>
					</Card>
				);
			})}
		</div>
	);
};
