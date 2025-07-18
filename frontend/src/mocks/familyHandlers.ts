import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";

export const familyHandlers = [
	// Mock the botanical groups endpoint
	http.get(buildUrl("/families/botanical-groups/"), ({ request }) => {
		const url = new URL(request.url);

		if (url.searchParams.get("abort") === "true") {
			return HttpResponse.json(
				{ detail: "Request cancelled" },
				{ status: 499 },
			);
		}

		// Successful response
		return HttpResponse.json([
			{
				id: "group-1",
				name: "Brassicaceae",
				recommended_rotation_years: 3,
				families: [
					{ id: "family-1", name: "Cabbage" },
					{ id: "family-2", name: "Broccoli" },
				],
			},
			{
				id: "group-2",
				name: "Solanaceae",
				recommended_rotation_years: 4,
				families: [
					{ id: "family-3", name: "Tomatoes" },
					{ id: "family-4", name: "Potatoes" },
				],
			},
			{
				id: "group-3",
				name: "Leguminosae",
				recommended_rotation_years: null,
				families: [
					{ id: "family-5", name: "Peas" },
					{ id: "family-6", name: "Beans" },
				],
			},
		]);
	}),

	http.options(buildUrl("/families/botanical-groups/"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Add handler for family details route
	http.get(buildUrl("/families/:familyId/"), ({ params }) => {
		const { familyId } = params;
		if (familyId === "family-1") {
			return HttpResponse.json({
				id: "family-1",
				name: "Cabbage",
				botanical_group: "Brassicaceae",
				recommended_rotation_years: 3,
				companion_families: ["Beans", "Peas"],
				antagonist_families: ["Tomatoes"],
				common_pests: [
					{ name: "Cabbage White Butterfly", treatment: "Netting" },
				],
				common_diseases: [
					{
						name: "Clubroot",
						symptoms: "Swollen roots",
						treatment: "Lime soil",
						prevention: "Crop rotation",
					},
				],
			});
		}
		if (familyId === "family-404") {
			return new HttpResponse(JSON.stringify({ detail: "Family not found" }), {
				status: 404,
				headers: { "Content-Type": "application/json" },
			});
		}
		// Default mock for other families
		return HttpResponse.json({
			id: familyId,
			name: "Unknown Family",
			botanical_group: "Unknown",
			recommended_rotation_years: null,
			companion_families: [],
			antagonist_families: [],
			common_pests: [],
			common_diseases: [],
		});
	}),
	http.options(buildUrl("/families/:familyId/"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
