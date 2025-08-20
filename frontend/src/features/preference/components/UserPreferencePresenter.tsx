import { FormError } from "@/components/FormError";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { FeedRead, DayRead, FeedDayRead } from "../forms/PreferenceSchema";

interface UserPreferencePresenterProps {
	feedTypes?: FeedRead[];
	days?: DayRead[];
	preferences?: FeedDayRead[];
	isLoading: boolean;
	isSaving: boolean;
	error: string | undefined;
	onUpdatePreference: (feedId: string, dayId: string) => void;
}

export default function UserPreferencePresenter({
	feedTypes = [],
	days = [],
	preferences = [],
	isLoading,
	isSaving,
	error,
	onUpdatePreference,
}: UserPreferencePresenterProps) {
	// Helper function to get current day for a feed type
	const getCurrentDayForFeed = (feedId: string): string => {
		const preference = preferences.find(
			(p: FeedDayRead) => p.feed_id === feedId,
		);
		return preference?.day_id || "";
	};

	// Helper function to get day name by ID
	const getDayName = (dayId: string): string => {
		return days.find((d: DayRead) => d.id === dayId)?.name || "";
	};

	if (isLoading) {
		return (
			<div className="container mx-auto max-w-4xl space-y-6 p-4">
				<Card>
					<CardHeader>
						<CardTitle>Feed Preferences</CardTitle>
					</CardHeader>
					<CardContent className="space-y-4">
						<p className="text-muted-foreground">Loading feed preferences...</p>
					</CardContent>
				</Card>
			</div>
		);
	}

	return (
		<div className="container mx-auto max-w-4xl space-y-6 p-4">
			<Card>
				<CardHeader>
					<CardTitle>Feed Preferences</CardTitle>
					<p className="text-muted-foreground">
						Set your preferred day for giving each type of plant feed
					</p>
				</CardHeader>
				<CardContent>
					{error && <FormError message={error} />}

					<div className="space-y-6">
						{feedTypes.map((feedType: FeedRead) => {
							const currentDayId = getCurrentDayForFeed(feedType.id);
							const currentDayName = getDayName(currentDayId);

							return (
								<div
									key={feedType.id}
									className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0 sm:space-x-4"
								>
									<div className="min-w-0 flex-1">
										<h3 className="font-medium text-foreground">
											{feedType.name}
										</h3>
									</div>

									<div className="flex items-center space-x-2 ml-auto">
										{Array.isArray(days) && days.length > 0 ? (
											<select
												className="w-48 h-10 border rounded-md px-3 bg-background"
												value={currentDayId || ""}
												onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
													onUpdatePreference(feedType.id, e.target.value)
												}
												disabled={isSaving}
											>
												<option value="">Select a day</option>
												{days.map((day: DayRead) => (
													<option key={day.id} value={day.id}>
														{day.name}
													</option>
												))}
											</select>
										) : (
											<div className="w-48 h-10 border rounded-md bg-muted flex items-center justify-center">
												<span className="text-sm text-muted-foreground">
													Loading days...
												</span>
											</div>
										)}
									</div>
								</div>
							);
						})}

						{feedTypes.length === 0 && !isLoading && (
							<p className="text-center text-muted-foreground">
								No feed types available
							</p>
						)}
					</div>

					{isSaving && (
						<div className="mt-4 text-center">
							<Button disabled size="sm">
								Saving...
							</Button>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
