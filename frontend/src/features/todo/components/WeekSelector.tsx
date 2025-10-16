import { Button } from "@/components/ui/Button";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";

interface WeekSelectorProps {
	currentWeekNumber: number;
	weekStartDate: string;
	weekEndDate: string;
	onWeekChange: (weekNumber: number) => void;
	minWeek?: number;
	maxWeek?: number;
}

export const WeekSelector = ({
	currentWeekNumber,
	weekStartDate,
	weekEndDate,
	onWeekChange,
	minWeek = 1,
	maxWeek = 52,
}: WeekSelectorProps) => {
	const handlePreviousWeek = () => {
		if (currentWeekNumber > minWeek) {
			onWeekChange(currentWeekNumber - 1);
		}
	};

	const handleNextWeek = () => {
		if (currentWeekNumber < maxWeek) {
			onWeekChange(currentWeekNumber + 1);
		}
	};

	const isPreviousDisabled = currentWeekNumber <= minWeek;
	const isNextDisabled = currentWeekNumber >= maxWeek;

	return (
		<div className="flex items-center justify-between bg-card border rounded-lg p-4 shadow-sm">
			<Button
				variant="outline"
				size="sm"
				onClick={handlePreviousWeek}
				disabled={isPreviousDisabled}
				className="flex items-center gap-2"
			>
				<ChevronLeft className="h-4 w-4" />
				Previous Week
			</Button>

			<div className="flex items-center gap-3">
				<Calendar className="h-5 w-5 text-muted-foreground" />
				<div className="text-center">
					<p className="text-sm font-medium">Week {currentWeekNumber}</p>
					<p className="text-xs text-muted-foreground">
						{weekStartDate} - {weekEndDate}
					</p>
				</div>
			</div>

			<Button
				variant="outline"
				size="sm"
				onClick={handleNextWeek}
				disabled={isNextDisabled}
				className="flex items-center gap-2"
			>
				Next Week
				<ChevronRight className="h-4 w-4" />
			</Button>
		</div>
	);
};
