import { Badge } from "../../../components/ui/Badge";
import type { VarietyList } from "../services/growGuideService";
import { Skeleton } from "../../../components/ui/Skeleton";
import {
	Alert,
	AlertDescription,
	AlertTitle,
} from "../../../components/ui/Alert";
import { Terminal, Leaf, Clock, Eye, EyeOff, Search } from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "../../../components/ui/Card";
import { Input } from "../../../components/ui/Input";
import { useState } from "react";

interface GrowGuideListPresenterProps {
	growGuides: VarietyList[];
	isLoading: boolean;
	isError: boolean;
}

export const GrowGuideListPresenter = ({
	growGuides,
	isLoading,
	isError,
}: GrowGuideListPresenterProps) => {
	const [searchTerm, setSearchTerm] = useState("");

	// Filter guides based on search term
	const filteredGuides = growGuides.filter((guide) =>
		guide.variety_name.toLowerCase().includes(searchTerm.toLowerCase()),
	);

	if (isLoading) {
		// Create an array of predefined unique keys for skeleton cards
		const skeletonKeys = [
			"skeleton-card-1",
			"skeleton-card-2",
			"skeleton-card-3",
			"skeleton-card-4",
			"skeleton-card-5",
			"skeleton-card-6",
		];

		return (
			<div className="space-y-4">
				<Skeleton className="h-8 w-1/4" />
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{skeletonKeys.map((key) => (
						<Card key={key}>
							<CardHeader>
								<Skeleton className="h-6 w-32" />
							</CardHeader>
							<CardContent className="space-y-3">
								<div className="flex items-center gap-2">
									<Skeleton className="h-4 w-4" />
									<Skeleton className="h-5 w-24" />
								</div>
								<div className="flex items-center gap-2">
									<Skeleton className="h-4 w-4" />
									<Skeleton className="h-5 w-16" />
								</div>
								<div className="flex items-center gap-2">
									<Skeleton className="h-4 w-4" />
									<Skeleton className="h-5 w-40" />
								</div>
							</CardContent>
						</Card>
					))}
				</div>
			</div>
		);
	}

	if (isError) {
		return (
			<div className="text-center py-10 space-y-4">
				<div className="mx-auto bg-primary w-16 h-16 rounded-full flex items-center justify-center">
					<Leaf className="h-8 w-8 text-primary-foreground" />
				</div>
				<p className="text-muted-foreground max-w-md mx-auto">
					You don't have any grow guides yet. Click the "Add New Guide" button
					above to create your first guide and start tracking your plants.
				</p>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{growGuides.length === 0 ? (
				<div className="text-center py-10 space-y-4">
					<div className="mx-auto bg-primary w-16 h-16 rounded-full flex items-center justify-center">
						<Leaf className="h-8 w-8 text-primary-foreground" />
					</div>
					<p className="text-muted-foreground max-w-md mx-auto">
						You don't have any grow guides yet. Click the "Add New Guide" button
						above to create your first guide and start tracking your plants.
					</p>
				</div>
			) : (
				<>
					<div className="relative">
						<Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search guides..."
							className="pl-10"
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
						/>
					</div>

					{filteredGuides.length === 0 ? (
						<div className="text-center py-10">
							<p className="text-muted-foreground">
								No grow guides found. Try a different search term.
							</p>
						</div>
					) : (
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
							{filteredGuides.map((guide) => (
								<Card
									key={guide.variety_id}
									className="hover:shadow-md transition-shadow cursor-pointer"
								>
									<CardHeader>
										<CardTitle>{guide.variety_name}</CardTitle>
										<CardDescription>
											{guide.lifecycle.lifecycle_name}
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-3">
										<div className="flex items-center gap-2">
											<Leaf className="h-4 w-4 text-green-600" />
											<span>{guide.lifecycle.lifecycle_name}</span>
										</div>
										<div className="flex items-center gap-2">
											{guide.is_public ? (
												<>
													<Eye className="h-4 w-4 text-blue-600" />
													<span>Public</span>
												</>
											) : (
												<>
													<EyeOff className="h-4 w-4 text-gray-600" />
													<span>Private</span>
												</>
											)}
										</div>
										<div className="flex items-center gap-2">
											<Clock className="h-4 w-4 text-orange-600" />
											<span>
												{new Date(guide.last_updated).toLocaleDateString()}
											</span>
										</div>
									</CardContent>
									<CardFooter>
										<Badge
											variant={guide.is_public ? "secondary" : "outline"}
											className="ml-auto"
										>
											{guide.is_public ? "Public" : "Private"}
										</Badge>
									</CardFooter>
								</Card>
							))}
						</div>
					)}
				</>
			)}
		</div>
	);
};
