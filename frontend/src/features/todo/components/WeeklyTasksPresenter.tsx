import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { VarietyTaskDetail } from "../types/todoTypes";
import {
	Sprout,
	Scissors,
	ShoppingBasket,
	Trash2,
	MoveHorizontal,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface WeeklyTasksPresenterProps {
	sowTasks: VarietyTaskDetail[];
	transplantTasks: VarietyTaskDetail[];
	harvestTasks: VarietyTaskDetail[];
	pruneTasks: VarietyTaskDetail[];
	compostTasks: VarietyTaskDetail[];
}

const TaskList = ({
	tasks,
	emptyMessage,
}: {
	tasks: VarietyTaskDetail[];
	emptyMessage: string;
}) => {
	if (tasks.length === 0) {
		return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
	}

	return (
		<div className="space-y-2">
			{tasks.map((task) => (
				<div
					key={task.variety_id}
					className="flex items-center justify-between p-3 bg-secondary/30 rounded-md hover:bg-secondary/50 transition-colors"
				>
					<div className="flex flex-col">
						<span className="font-medium">{task.variety_name}</span>
						<span className="text-sm text-muted-foreground">
							{task.family_name}
						</span>
					</div>
				</div>
			))}
		</div>
	);
};

export const WeeklyTasksPresenter = ({
	sowTasks,
	transplantTasks,
	harvestTasks,
	pruneTasks,
	compostTasks,
}: WeeklyTasksPresenterProps) => {
	const hasAnyTasks =
		sowTasks.length > 0 ||
		transplantTasks.length > 0 ||
		harvestTasks.length > 0 ||
		pruneTasks.length > 0 ||
		compostTasks.length > 0;

	if (!hasAnyTasks) {
		return (
			<Card>
				<CardContent className="pt-6">
					<p className="text-center text-muted-foreground">
						No weekly tasks scheduled for this week.
					</p>
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{sowTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Sprout className="h-5 w-5 text-green-600" />
						<CardTitle className="text-lg">Sow</CardTitle>
						<Badge variant="secondary" className="ml-auto">
							{sowTasks.length}
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList tasks={sowTasks} emptyMessage="No sowing tasks" />
					</CardContent>
				</Card>
			)}

			{transplantTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<MoveHorizontal className="h-5 w-5 text-blue-600" />
						<CardTitle className="text-lg">Transplant</CardTitle>
						<Badge variant="secondary" className="ml-auto">
							{transplantTasks.length}
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={transplantTasks}
							emptyMessage="No transplant tasks"
						/>
					</CardContent>
				</Card>
			)}

			{harvestTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<ShoppingBasket className="h-5 w-5 text-orange-600" />
						<CardTitle className="text-lg">Harvest</CardTitle>
						<Badge variant="secondary" className="ml-auto">
							{harvestTasks.length}
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList tasks={harvestTasks} emptyMessage="No harvest tasks" />
					</CardContent>
				</Card>
			)}

			{pruneTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Scissors className="h-5 w-5 text-purple-600" />
						<CardTitle className="text-lg">Prune</CardTitle>
						<Badge variant="secondary" className="ml-auto">
							{pruneTasks.length}
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList tasks={pruneTasks} emptyMessage="No pruning tasks" />
					</CardContent>
				</Card>
			)}

			{compostTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Trash2 className="h-5 w-5 text-brown-600" />
						<CardTitle className="text-lg">Compost</CardTitle>
						<Badge variant="secondary" className="ml-auto">
							{compostTasks.length}
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList tasks={compostTasks} emptyMessage="No compost tasks" />
					</CardContent>
				</Card>
			)}
		</div>
	);
};
