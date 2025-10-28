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
	onVarietyClick?: (varietyId: string) => void;
}

type Tone = "primary" | "muted" | "accent" | "destructive";

// Accessible tone styling that respects theme tokens and improves contrast
const toneClasses: Record<
	Tone,
	{ bg: string; border: string; hoverBg: string }
> = {
	primary: {
		bg: "bg-primary/15",
		border: "border-primary/40",
		hoverBg: "hover:bg-primary/25",
	},
	muted: {
		bg: "bg-muted/15",
		border: "border-muted/40",
		hoverBg: "hover:bg-muted/25",
	},
	accent: {
		bg: "bg-accent/20",
		border: "border-accent/40",
		hoverBg: "hover:bg-accent/30",
	},
	destructive: {
		bg: "bg-destructive/15",
		border: "border-destructive/40",
		hoverBg: "hover:bg-destructive/25",
	},
};

const TaskList = ({
	tasks,
	emptyMessage,
	tone,
	onVarietyClick,
}: {
	tasks: VarietyTaskDetail[];
	emptyMessage: string;
	tone: Tone;
	onVarietyClick?: (varietyId: string) => void;
}) => {
	if (tasks.length === 0) {
		return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
	}

	const t = toneClasses[tone];

	return (
		<div className="space-y-2">
			{tasks.map((task) => (
				<button
					key={task.variety_id}
					type="button"
					onClick={() => onVarietyClick?.(task.variety_id)}
					className={`w-full text-left flex items-center justify-between p-3 rounded-md border ${t.bg} ${t.border} text-foreground ${t.hoverBg} focus:outline-none focus-visible:ring-2 focus-visible:ring-ring/80 focus-visible:ring-offset-2 focus-visible:ring-offset-background cursor-pointer`}
				>
					<span className={"font-medium text-foreground"}>
						{task.variety_name}
					</span>
					<span className="text-sm text-muted-foreground">
						{task.family_name}
					</span>
				</button>
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
	onVarietyClick,
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
		<div className="space-y-4">
			{sowTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Sprout className="h-5 w-5 text-primary" />
						<CardTitle className="text-lg">Sow</CardTitle>
						<Badge
							variant="outline"
							className="ml-auto bg-primary/20 text-foreground border-primary/40"
						>
							<Sprout className="h-3 w-3 mr-1" />
							{sowTasks.length} Sow
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={sowTasks}
							emptyMessage="No sowing tasks"
							tone="primary"
							onVarietyClick={onVarietyClick}
						/>
					</CardContent>
				</Card>
			)}

			{transplantTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<MoveHorizontal className="h-5 w-5 text-muted" />
						<CardTitle className="text-lg">Transplant</CardTitle>
						<Badge
							variant="outline"
							className="ml-auto bg-muted/20 text-foreground border-muted/40"
						>
							<MoveHorizontal className="h-3 w-3 mr-1" />
							{transplantTasks.length} Transplant
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={transplantTasks}
							emptyMessage="No transplant tasks"
							tone="muted"
							onVarietyClick={onVarietyClick}
						/>
					</CardContent>
				</Card>
			)}

			{harvestTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<ShoppingBasket className="h-5 w-5 text-accent" />
						<CardTitle className="text-lg">Harvest</CardTitle>
						<Badge
							variant="outline"
							className="ml-auto bg-accent/25 text-foreground border-accent/40"
						>
							<ShoppingBasket className="h-3 w-3 mr-1" />
							{harvestTasks.length} Harvest
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={harvestTasks}
							emptyMessage="No harvest tasks"
							tone="accent"
							onVarietyClick={onVarietyClick}
						/>
					</CardContent>
				</Card>
			)}

			{pruneTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Scissors className="h-5 w-5 text-accent" />
						<CardTitle className="text-lg">Prune</CardTitle>
						<Badge
							variant="outline"
							className="ml-auto bg-accent/25 text-foreground border-accent/40"
						>
							<Scissors className="h-3 w-3 mr-1" />
							{pruneTasks.length} Prune
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={pruneTasks}
							emptyMessage="No pruning tasks"
							tone="accent"
							onVarietyClick={onVarietyClick}
						/>
					</CardContent>
				</Card>
			)}

			{compostTasks.length > 0 && (
				<Card>
					<CardHeader className="flex flex-row items-center space-x-2 pb-3">
						<Trash2 className="h-5 w-5 text-destructive" />
						<CardTitle className="text-lg">Compost</CardTitle>
						<Badge
							variant="outline"
							className="ml-auto bg-destructive/20 text-foreground border-destructive/40"
						>
							<Trash2 className="h-3 w-3 mr-1" />
							{compostTasks.length} Compost
						</Badge>
					</CardHeader>
					<CardContent>
						<TaskList
							tasks={compostTasks}
							emptyMessage="No compost tasks"
							tone="destructive"
							onVarietyClick={onVarietyClick}
						/>
					</CardContent>
				</Card>
			)}
		</div>
	);
};
