import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Loader2 } from "lucide-react";
import type { IFamilyInfo } from "../services/FamilyService";
import { Link } from "react-router-dom";

interface Props {
	readonly data: IFamilyInfo | null;
	readonly isLoading: boolean;
	readonly error: Error | null;
	readonly isSuccess: boolean;
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

	// Guard for missing botanical_group
	const hasBotanicalGroup =
		data.botanical_group && typeof data.botanical_group === "object";

	return (
		<div className="w-full max-w-2xl mx-auto min-h-[32rem] flex flex-col">
			<h1 className="text-3xl font-bold mb-2 capitalize">{data.name}</h1>
			{hasBotanicalGroup && (
				<div className="mb-4 text-muted-foreground">
					<span>
						Group:{" "}
						<Link
							to="/botanical_groups"
							className="capitalize underline underline-offset-4 font-semibold text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline-2 focus-visible:outline-ring transition-colors"
						>
							{data.botanical_group.name}
						</Link>
					</span>

					<span>
						Rotation:{" "}
						{data.botanical_group.recommended_rotation_years !== null &&
						data.botanical_group.recommended_rotation_years !== undefined
							? `${data.botanical_group.recommended_rotation_years} year(s)`
							: "Perennial"}
					</span>
				</div>
			)}
			<div className="flex flex-col md:flex-row gap-4 mb-6">
				<div className="flex-1">
					<h2 className="font-semibold mb-1">Companion Families</h2>
					{data.companion_to && data.companion_to.length > 0 ? (
						<ul className="list-disc pl-5">
							{data.companion_to.map((fam) => (
								<li key={fam.id} className="capitalize">
									<Link
										to={`/family/${fam.id}`}
										className="underline underline-offset-4 text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline-2 focus-visible:outline-ring transition-colors"
									>
										{fam.name}
									</Link>
								</li>
							))}
						</ul>
					) : (
						<p className="text-sm text-muted-foreground">
							No companion families listed.
						</p>
					)}
				</div>
				<div className="flex-1">
					<h2 className="font-semibold mb-1">Antagonist Families</h2>
					{data.antagonises && data.antagonises.length > 0 ? (
						<ul className="list-disc pl-5">
							{data.antagonises.map((fam) => (
								<li key={fam.id} className="capitalize">
									<Link
										to={`/family/${fam.id}`}
										className="underline underline-offset-4 text-primary dark:text-primary-foreground hover:text-interactive-foreground dark:hover:text-interactive-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring transition-colors"
									>
										{fam.name}
									</Link>
								</li>
							))}
						</ul>
					) : (
						<p className="text-sm text-muted-foreground">
							No antagonist families listed.
						</p>
					)}
				</div>
			</div>
			<div className="mb-6">
				<h2 className="font-semibold mb-2">Diseases</h2>
				{data.diseases && data.diseases.length > 0 ? (
					<ul className="space-y-3">
						{data.diseases.map((disease) => (
							<li key={disease.id} className="border rounded p-3">
								<h3 className="text-lg font-bold capitalize mb-2 text-foreground bg-accent/20 p-1 rounded">
									{disease.name}
								</h3>
								<div className="grid gap-1">
									<div>
										<strong className="text-sm">Symptoms:</strong>{" "}
										{disease.symptoms && disease.symptoms.length > 0 ? (
											disease.symptoms.map((s) => s.name).join(", ")
										) : (
											<span className="text-muted-foreground">None listed</span>
										)}
									</div>
									<div>
										<strong className="text-sm">Treatments:</strong>{" "}
										{disease.treatments && disease.treatments.length > 0 ? (
											disease.treatments.map((t) => t.name).join(", ")
										) : (
											<span className="text-muted-foreground">None listed</span>
										)}
									</div>
									<div>
										<strong className="text-sm">Preventions:</strong>{" "}
										{disease.preventions && disease.preventions.length > 0 ? (
											disease.preventions.map((p) => p.name).join(", ")
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
				)}
			</div>
			<div>
				<h2 className="font-semibold mb-2">Pests</h2>
				{data.pests && data.pests.length > 0 ? (
					<ul className="space-y-3">
						{data.pests.map((pest) => (
							<li key={pest.id} className="border rounded p-3">
								<h3 className="text-lg font-bold capitalize mb-2 text-foreground bg-accent/20 p-1 rounded">
									{pest.name}
								</h3>
								<div className="grid gap-1">
									<div>
										<strong className="text-sm">Treatments:</strong>{" "}
										{pest.treatments && pest.treatments.length > 0 ? (
											pest.treatments.map((t) => t.name).join(", ")
										) : (
											<span className="text-muted-foreground">None listed</span>
										)}
									</div>
									<div>
										<strong className="text-sm">Preventions:</strong>{" "}
										{pest.preventions && pest.preventions.length > 0 ? (
											pest.preventions.map((p) => p.name).join(", ")
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
				)}
			</div>
		</div>
	);
}
