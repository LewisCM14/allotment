import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Sprout, Plus, BookOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";

export const WelcomeEmptyState = () => {
	const navigate = useNavigate();

	return (
		<div className="flex items-center justify-center min-h-[60vh]">
			<Card className="max-w-2xl w-full">
				<CardContent className="pt-12 pb-12 px-8">
					<div className="text-center space-y-6">
						{/* Icon */}
						<div className="flex justify-center">
							<div className="rounded-full bg-primary/10 p-6">
								<Sprout className="h-16 w-16 text-primary" />
							</div>
						</div>

						{/* Welcome Message */}
						<div className="space-y-3">
							<h1 className="text-3xl font-bold tracking-tight">
								Welcome to Your Garden Hub!
							</h1>
							<p className="text-lg text-muted-foreground max-w-md mx-auto">
								Start your gardening journey by creating your first grow guide.
								Once you have active varieties, your weekly tasks will appear
								here.
							</p>
						</div>

						{/* Steps */}
						<div className="bg-secondary/30 rounded-lg p-6 mt-8 text-left max-w-md mx-auto">
							<h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground mb-4">
								Getting Started
							</h3>
							<div className="space-y-3">
								<div className="flex items-start gap-3">
									<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
										1
									</div>
									<div>
										<p className="font-medium">Create a Grow Guide</p>
										<p className="text-sm text-muted-foreground">
											Add details about the plants you want to grow
										</p>
									</div>
								</div>
								<div className="flex items-start gap-3">
									<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
										2
									</div>
									<div>
										<p className="font-medium">Activate Your Varieties</p>
										<p className="text-sm text-muted-foreground">
											Mark varieties as active to track their care schedule
										</p>
									</div>
								</div>
								<div className="flex items-start gap-3">
									<div className="rounded-full bg-primary text-primary-foreground w-6 h-6 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-0.5">
										3
									</div>
									<div>
										<p className="font-medium">View Your Tasks</p>
										<p className="text-sm text-muted-foreground">
											Check this page to see weekly sowing, watering, and
											harvesting tasks
										</p>
									</div>
								</div>
							</div>
						</div>

						{/* Action Buttons */}
						<div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
							<Button
								size="lg"
								onClick={() => navigate("/grow-guides")}
								className="gap-2"
							>
								<Plus className="h-5 w-5" />
								Create A Guide
							</Button>
							<Button
								size="lg"
								variant="outline"
								onClick={() => navigate("/botanical_groups")}
								className="gap-2"
							>
								<BookOpen className="h-5 w-5" />
								Explore Plant Families
							</Button>
						</div>

						{/* Optional help text */}
						<p className="text-xs text-muted-foreground pt-4">
							Need help? Check out the plant families to learn which vegetables
							grow well together.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);
};
