import { useState } from "react";
import {
	useCreateVariety,
	useDeleteVariety,
	useToggleVarietyPublic,
	useUpdateVariety,
	useUserVarieties,
	useVarietyOptions,
} from "../hooks/useGrowGuide";
import GrowGuidePresenter from "./GrowGuidePresenter";
import type { CreateVarietyFormData, UpdateVarietyFormData } from "../schemas/varietySchemas";
import type { VarietyListRead } from "../types/growGuideTypes";
import { formatError } from "@/utils/errorUtils";

export default function GrowGuideContainer() {
	const [isFormOpen, setIsFormOpen] = useState(false);
	const [editingVariety, setEditingVariety] = useState<VarietyListRead | undefined>();
	const [formError, setFormError] = useState<string | undefined>();

	// Queries
	const {
		data: varieties = [],
		isLoading: varietiesLoading,
		error: varietiesError,
	} = useUserVarieties();
	
	const {
		data: options,
		isLoading: optionsLoading,
		error: optionsError,
	} = useVarietyOptions();

	// Mutations
	const createMutation = useCreateVariety();
	const updateMutation = useUpdateVariety();
	const deleteMutation = useDeleteVariety();
	const togglePublicMutation = useToggleVarietyPublic();

	const isLoading = varietiesLoading || optionsLoading;
	const error = varietiesError || optionsError ? formatError(varietiesError || optionsError) : undefined;
	const isSubmitting = createMutation.isPending || updateMutation.isPending;

	const handleCreateNew = () => {
		setEditingVariety(undefined);
		setFormError(undefined);
		setIsFormOpen(true);
	};

	const handleEdit = (variety: VarietyListRead) => {
		setEditingVariety(variety);
		setFormError(undefined);
		setIsFormOpen(true);
	};

	const handleView = (variety: VarietyListRead) => {
		// TODO: Implement detailed view in Stage 3
		console.log("View variety:", variety);
	};

	const handleDelete = (varietyId: string) => {
		// TODO: Add confirmation dialog
		deleteMutation.mutate(varietyId);
	};

	const handleTogglePublic = (varietyId: string) => {
		togglePublicMutation.mutate(varietyId);
	};

	const handleFormClose = () => {
		setIsFormOpen(false);
		setEditingVariety(undefined);
		setFormError(undefined);
	};

	const handleFormSubmit = (data: CreateVarietyFormData | UpdateVarietyFormData) => {
		setFormError(undefined);

		if (editingVariety) {
			// Update existing variety
			updateMutation.mutate(
				{
					varietyId: editingVariety.variety_id,
					varietyData: data as UpdateVarietyFormData,
				},
				{
					onSuccess: () => {
						handleFormClose();
					},
					onError: (error) => {
						setFormError(formatError(error));
					},
				}
			);
		} else {
			// Create new variety
			createMutation.mutate(data as CreateVarietyFormData, {
				onSuccess: () => {
					handleFormClose();
				},
				onError: (error) => {
					setFormError(formatError(error));
				},
			});
		}
	};

	return (
		<GrowGuidePresenter
			varieties={varieties}
			options={options}
			isLoading={isLoading}
			error={error}
			isFormOpen={isFormOpen}
			editingVariety={editingVariety}
			isSubmitting={isSubmitting}
			formError={formError}
			onCreateNew={handleCreateNew}
			onEdit={handleEdit}
			onView={handleView}
			onDelete={handleDelete}
			onTogglePublic={handleTogglePublic}
			onFormClose={handleFormClose}
			onFormSubmit={handleFormSubmit}
		/>
	);
}
