import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Leaf, Plus, BookOpen } from "lucide-react";
import { memo } from "react";

interface GrowGuideEmptyStateProps {
	onAddNew: () => void;
}

export const GrowGuideEmptyState = memo(
	({ onAddNew }: GrowGuideEmptyStateProps) => {
		return (
			<div className="flex items-center justify-center min-h-[50vh]">
				<Card className="max-w-2xl w-full">
					<CardContent className="pt-12 pb-12 px-8">
						<div className="text-center space-y-6">
							{/* Explicit empty-state copy to satisfy tests and aid discoverability */}
							<p className="text-sm text-muted-foreground">
								You don't have any grow guides yet. Get started by creating your
								first grow guide.
							</p>
							{/* Icon */}
							<div className="flex justify-center">
								<div className="rounded-full bg-primary/10 p-6">
									<Leaf className="h-16 w-16 text-primary" />
								</div>
							</div>

							{/* Welcome Message */}
							<div className="space-y-3">
								<h2 className="text-3xl font-bold tracking-tight">
									Start Your Garden Library
								</h2>
								<p className="text-lg text-muted-foreground max-w-md mx-auto">
									Create guides to track planting schedules, care instructions,
									and harvest times for all your favorite vegetables and herbs.
								</p>
							</div>

							{/* Steps */}
							<div className="bg-secondary/30 rounded-lg p-6 mt-8 text-left max-w-md mx-auto">
								<h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground mb-4">
									What You'll Track
								</h3>
								<div className="space-y-3">
									<div className="flex items-start gap-3">
										<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
											📅
										</div>
										<div>
											<p className="font-medium">Planting & Harvest Windows</p>
											<p className="text-sm text-muted-foreground">
												Know exactly when to sow, transplant, and harvest
											</p>
										</div>
									</div>
									<div className="flex items-start gap-3">
										<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
											💧
										</div>
										<div>
											<p className="font-medium">Watering & Feeding Schedule</p>
											<p className="text-sm text-muted-foreground">
												Set custom frequencies for each plant's needs
											</p>
										</div>
									</div>
									<div className="flex items-start gap-3">
										<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
											🌱
										</div>
										<div>
											<p className="font-medium">Growing Requirements</p>
											<p className="text-sm text-muted-foreground">
												Soil pH, spacing, depth, and temperature preferences
											</p>
										</div>
									</div>
								</div>
							</div>

							{/* Action Buttons */}
							<div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
								<Button
									size="lg"
									onClick={onAddNew}
									className="gap-2 text-white"
								>
									<Plus className="h-5 w-5 text-white" />
									Create Your First Guide
								</Button>
								<Button size="lg" variant="outline" className="gap-2" asChild>
									<a href="/botanical_groups">
										<BookOpen className="h-5 w-5" />
										Explore Plant Families
									</a>
								</Button>
							</div>

							{/* Optional help text */}
							<p className="text-xs text-muted-foreground pt-4">
								Once you create a guide, you can activate it to see weekly tasks
								on your home page.
							</p>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	},
);
