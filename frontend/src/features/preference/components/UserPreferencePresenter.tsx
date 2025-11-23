import { FormError } from "@/components/FormError";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type {
	IFeedType,
	IDay,
	IUserFeedPreference,
} from "../forms/PreferenceSchema";

interface UserPreferencePresenterProps {
	readonly feedTypes?: ReadonlyArray<IFeedType>;
	readonly days?: ReadonlyArray<IDay>;
	readonly preferences?: ReadonlyArray<IUserFeedPreference>;
	readonly isLoading: boolean;
	readonly isSaving: boolean;
	readonly error?: string;
	readonly onUpdatePreference: (feedId: string, dayId: string) => void;
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
			(p: IUserFeedPreference) => p.feed_id === feedId,
		);
		return preference?.day_id ?? "";
	};

	if (isLoading) {
		return (
			<div className="flex justify-center items-center h-64">
				<div className="w-full max-w-2xl">
					<Card>
						<CardHeader>
							<CardTitle className="text-2xl">Feed Preferences</CardTitle>
							<p className="text-muted-foreground">
								Loading feed preferences...
							</p>
						</CardHeader>
					</Card>
				</div>
			</div>
		);
	}

	return (
		<div className="w-full max-w-2xl mx-auto space-y-6 p-4">
			<Card className="w-full">
				<CardHeader>
					<CardTitle className="text-2xl">Feed Preferences</CardTitle>
					<p className="text-muted-foreground">
						Set your preferred day for giving each type of plant feed
					</p>
				</CardHeader>
				<CardContent>
					{error && <FormError message={error} className="mb-4" />}

					<div className="space-y-6">
						{feedTypes.map((feedType: IFeedType) => {
							const currentDayId = getCurrentDayForFeed(feedType.id);

							return (
								<div
									key={feedType.id}
									className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0 sm:space-x-4 border-b border-border pb-4"
								>
									<div className="min-w-0 flex-1">
										<h3 className="font-medium text-lg text-foreground">
											{feedType.name}
										</h3>
									</div>

									<div className="flex items-center space-x-2 ml-auto">
										{Array.isArray(days) && days.length > 0 ? (
											<select
												className="w-48 h-10 border rounded-md px-3 bg-background text-lg"
												value={currentDayId || ""}
												onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
													onUpdatePreference(feedType.id, e.target.value)
												}
												disabled={isSaving}
											>
												<option value="" disabled>
													Select a day
												</option>
												{days.map((day: IDay) => (
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
							<Button disabled size="sm" className="text-white">
								Saving...
							</Button>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
