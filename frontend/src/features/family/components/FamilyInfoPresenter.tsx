import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Loader2 } from "lucide-react";
import type { IFamilyInfo } from "../services/FamilyService";
import { Link } from "react-router-dom";

// Types matching backend schema
type Symptom = { symptom_id: string; symptom_name: string };
type Treatment = { intervention_id: string; intervention_name: string };
type Prevention = { intervention_id: string; intervention_name: string };
type Disease = {
	disease_id: string;
	disease_name: string;
	symptoms?: Symptom[];
	treatments?: Treatment[];
	preventions?: Prevention[];
};
type Pest = {
	pest_id: string;
	pest_name: string;
	treatments?: Treatment[];
	preventions?: Prevention[];
};

interface Props {
	readonly data: IFamilyInfo | null;
	readonly isLoading: boolean;
	readonly error: Error | null;
	readonly isSuccess: boolean;
}

interface ListSectionProps<T> {
	readonly title: string;
	readonly items: ReadonlyArray<T>;
	readonly renderItem: (item: T) => React.ReactNode;
	readonly emptyText: string;
}

function ListSection<T extends { family_id: string; family_name: string }>({
	title,
	items,
	renderItem,
	emptyText,
}: Readonly<ListSectionProps<T>>) {
	return (
		<div className="flex-1">
			<h2 className="font-semibold mb-1">{title}</h2>
			{items && items.length > 0 ? (
				<ul className="list-disc pl-5">{items.map(renderItem)}</ul>
			) : (
				<p className="text-sm text-muted-foreground">{emptyText}</p>
			)}
		</div>
	);
}

function DiseaseList({ diseases }: { diseases: Disease[] }) {
	return diseases && diseases.length > 0 ? (
		<ul className="space-y-3">
			{diseases.map((disease) => (
				<li key={disease.disease_id} className="border rounded p-3">
					<h3 className="text-lg font-bold capitalize mb-2 text-foreground bg-accent/20 p-1 rounded">
						{disease.disease_name}
					</h3>
					<div className="grid gap-1">
						<div>
							<strong className="text-sm">Symptoms:</strong>{" "}
							{disease.symptoms && disease.symptoms.length > 0 ? (
								disease.symptoms.map((s) => s.symptom_name).join(", ")
							) : (
								<span className="text-muted-foreground">None listed</span>
							)}
						</div>
						<div>
							<strong className="text-sm">Treatments:</strong>{" "}
							{disease.treatments && disease.treatments.length > 0 ? (
								disease.treatments.map((t) => t.intervention_name).join(", ")
							) : (
								<span className="text-muted-foreground">None listed</span>
							)}
						</div>
						<div>
							<strong className="text-sm">Preventions:</strong>{" "}
							{disease.preventions && disease.preventions.length > 0 ? (
								disease.preventions.map((p) => p.intervention_name).join(", ")
							) : (
								<span className="text-muted-foreground">None listed</span>
							)}
						</div>
					</div>
				</li>
			))}
		</ul>
	) : (
		<p className="text-sm text-muted-foreground">No diseases listed.</p>
	);
}

function PestList({ pests }: { pests: Pest[] }) {
	return pests && pests.length > 0 ? (
		<ul className="space-y-3">
			{pests.map((pest) => (
				<li key={pest.pest_id} className="border rounded p-3">
					<h3 className="text-lg font-bold capitalize mb-2 text-foreground bg-accent/20 p-1 rounded">
						{pest.pest_name}
					</h3>
					<div className="grid gap-1">
						<div>
							<strong className="text-sm">Treatments:</strong>{" "}
							{pest.treatments && pest.treatments.length > 0 ? (
								pest.treatments.map((t) => t.intervention_name).join(", ")
							) : (
								<span className="text-muted-foreground">None listed</span>
							)}
						</div>
						<div>
							<strong className="text-sm">Preventions:</strong>{" "}
							{pest.preventions && pest.preventions.length > 0 ? (
								pest.preventions.map((p) => p.intervention_name).join(", ")
							) : (
								<span className="text-muted-foreground">None listed</span>
							)}
						</div>
					</div>
				</li>
			))}
		</ul>
	) : (
		<p className="text-sm text-muted-foreground">No pests listed.</p>
	);
}

export function FamilyInfoPresenter({
	data,
	isLoading,
	error,
	isSuccess,
}: Props) {
	if (isLoading) {
		return (
			<div className="flex justify-center items-center h-64">
				<Loader2 className="h-8 w-8 animate-spin text-primary" />
				<p className="ml-2">Loading family information...</p>
			</div>
		);
	}
	if (error) {
		return (
			<Alert variant="destructive" className="my-4">
				<AlertTitle>Error</AlertTitle>
				<AlertDescription>
					Failed to load family information: {error.message}
				</AlertDescription>
			</Alert>
		);
	}
	if (isSuccess && !data) {
		return (
			<Alert className="my-4">
				<AlertTitle>Not Found</AlertTitle>
				<AlertDescription>
					The requested family information could not be found.
				</AlertDescription>
			</Alert>
		);
	}
	if (!data) return null;

	const hasBotanicalGroup =
		data.botanical_group && typeof data.botanical_group === "object";

	return (
		<div className="w-full max-w-2xl mx-auto min-h-[32rem] flex flex-col">
			<h1 className="text-3xl font-bold mb-2 capitalize">{data.family_name}</h1>
			{hasBotanicalGroup && (
				<div className="mb-4 text-muted-foreground">
					<span>
						Group:{" "}
						<Link
							to="/botanical_groups"
							className="capitalize underline underline-offset-4 font-semibold text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline-2 focus-visible:outline-ring transition-colors"
						>
							{data.botanical_group.botanical_group_name}
						</Link>
					</span>
					<span>
						{" "}
						Rotation:{" "}
						{data.botanical_group.rotate_years !== null &&
						data.botanical_group.rotate_years !== undefined
							? `${data.botanical_group.rotate_years} year(s)`
							: "Perennial"}
					</span>
				</div>
			)}
			<div className="flex flex-col md:flex-row gap-4 mb-6">
				<ListSection
					title="Companion Families"
					items={data.companion_to || []}
					renderItem={(fam) => (
						<li key={fam.family_id} className="capitalize">
							<Link
								to={`/family/${fam.family_id}`}
								className="underline underline-offset-4 text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline-2 focus-visible:outline-ring transition-colors"
							>
								{fam.family_name}
							</Link>
						</li>
					)}
					emptyText="No companion families listed."
				/>
				<ListSection
					title="Antagonist Families"
					items={data.antagonises || []}
					renderItem={(fam) => (
						<li key={fam.family_id} className="capitalize">
							<Link
								to={`/family/${fam.family_id}`}
								className="underline underline-offset-4 text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline-2 focus-visible:outline-ring transition-colors"
							>
								{fam.family_name}
							</Link>
						</li>
					)}
					emptyText="No antagonist families listed."
				/>
			</div>
			<div className="mb-6">
				<h2 className="font-semibold mb-2">Diseases</h2>
				<DiseaseList diseases={data.diseases || []} />
			</div>
			<div>
				<h2 className="font-semibold mb-2">Pests</h2>
				<PestList pests={data.pests || []} />
			</div>
		</div>
	);
}
