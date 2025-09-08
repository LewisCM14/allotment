import { PageLayout } from "../../../components/layouts/PageLayout";
import { GrowGuideListContainer } from "../components/GrowGuideListContainer";
import { Button } from "../../../components/ui/Button";
import { Plus } from "lucide-react";
import { useState } from "react";
import { GrowGuideForm } from "../forms/GrowGuideForm";

const GrowGuides = () => {
	const [isFormOpen, setIsFormOpen] = useState(false);

	return (
		<PageLayout>
			<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
				<div>
					<h1 className="text-3xl font-bold tracking-tight">Grow Guides</h1>
					<p className="text-muted-foreground mt-1">
						Manage and explore your plant grow guides
					</p>
				</div>
				<Button onClick={() => setIsFormOpen(true)}>
					<Plus className="mr-2 h-4 w-4" />
					Add New Guide
				</Button>
			</div>
			<GrowGuideListContainer />

			{/* Add new grow guide form dialog */}
			<GrowGuideForm isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} />
		</PageLayout>
	);
};
export default GrowGuides;
