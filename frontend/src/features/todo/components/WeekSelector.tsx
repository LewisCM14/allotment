import { Button } from "@/components/ui/Button";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";

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
	// Helper to compute ISO week number for today's date
	const getISOWeek = (date: Date): number => {
		const d = new Date(
			Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()),
		);
		const dayNum = d.getUTCDay() || 7; // Make Sunday = 7
		d.setUTCDate(d.getUTCDate() + 4 - dayNum);
		const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
		return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
	};

	const weeks = useMemo(
		() => Array.from({ length: maxWeek - minWeek + 1 }, (_, i) => minWeek + i),
		[minWeek, maxWeek],
	);

	const selectedWeekRef = useRef<HTMLButtonElement | null>(null);
	const scrollContainerRef = useRef<HTMLDivElement | null>(null);

	const handlePreviousWeek = () => {
		// Wrap from min -> max
		const nextWeek =
			currentWeekNumber === minWeek ? maxWeek : currentWeekNumber - 1;
		onWeekChange(nextWeek);
	};

	const handleNextWeek = () => {
		// Wrap from max -> min
		const nextWeek =
			currentWeekNumber === maxWeek ? minWeek : currentWeekNumber + 1;
		onWeekChange(nextWeek);
	};

	// Only disable if there is a single week in range
	const hasMultipleWeeks = maxWeek > minWeek;
	const isPreviousDisabled = !hasMultipleWeeks;
	const isNextDisabled = !hasMultipleWeeks;

	// Keep selected week pill in view
	// biome-ignore lint/correctness/useExhaustiveDependencies: Re-run when selected week changes to keep it centered
	useEffect(() => {
		const el = selectedWeekRef.current;
		if (el && typeof el.scrollIntoView === "function") {
			el.scrollIntoView({
				behavior: "smooth",
				inline: "center",
				block: "nearest",
			});
		}
	}, [currentWeekNumber]);

	const onWheelHorizontal = (e: React.WheelEvent<HTMLDivElement>) => {
		const el = scrollContainerRef.current;
		if (!el) return;

		e.preventDefault();
		e.stopPropagation();
		const delta =
			Math.abs(e.deltaY) >= Math.abs(e.deltaX) ? e.deltaY : e.deltaX;
		el.scrollLeft += delta;
	};

	// Keyboard navigation for each week pill
	const onPillKeyDown = (
		e: React.KeyboardEvent<HTMLButtonElement>,
		week: number,
	) => {
		if (e.key === "ArrowLeft") {
			e.preventDefault();
			const prev = week === minWeek ? maxWeek : week - 1;
			onWeekChange(prev);
		} else if (e.key === "ArrowRight") {
			e.preventDefault();
			const next = week === maxWeek ? minWeek : week + 1;
			onWeekChange(next);
		}
	};

	// Compute the actual current week number, clamped into [minWeek, maxWeek]
	const todayWeekRaw = getISOWeek(new Date());
	const actualWeekNumber = Math.min(Math.max(todayWeekRaw, minWeek), maxWeek);

	return (
		<div className="space-y-3 bg-card border rounded-lg p-4 shadow-sm">
			<div className="flex items-center justify-between">
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

			{/* Carousel */}
			<div
				aria-label="Select week number"
				className="flex items-center gap-2 overflow-x-auto rounded-2xl border px-3 py-2 bg-background/50 scrollbar-thin touch-pan-x"
				ref={scrollContainerRef}
				onWheelCapture={onWheelHorizontal}
				style={{ overscrollBehavior: "contain" }}
			>
				{weeks.map((week) => {
					const isSelected = week === currentWeekNumber;
					const isActual = week === actualWeekNumber;
					const disabled = week < minWeek || week > maxWeek;
					const baseClasses =
						"h-8 min-w-8 px-2 text-sm rounded-full border transition-colors outline-none focus-visible:ring-ring/50 focus-visible:ring-[3px] cursor-pointer disabled:cursor-not-allowed disabled:opacity-50";
					let variantClasses: string;
					if (isSelected) {
						variantClasses =
							"bg-primary text-primary-foreground border-primary hover:brightness-105";
					} else if (isActual) {
						variantClasses =
							"bg-accent text-accent-foreground border-accent ring-2 ring-accent/60 hover:brightness-105";
					} else {
						variantClasses =
							"bg-card text-foreground border-border hover:bg-accent/15 hover:border-accent/40";
					}
					return (
						<button
							key={week}
							type="button"
							aria-pressed={isSelected}
							disabled={disabled}
							ref={isSelected ? selectedWeekRef : undefined}
							onClick={() => onWeekChange(week)}
							onKeyDown={(e) => onPillKeyDown(e, week)}
							className={`${baseClasses} ${variantClasses}`}
							title={`Week ${week}`}
						>
							{week}
						</button>
					);
				})}
			</div>
		</div>
	);
};
