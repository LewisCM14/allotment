import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk, jsonError } from "./responseHelpers";
import type {
	VarietyList,
	GrowGuideDetail,
	GrowGuideOptions,
} from "../features/grow_guide/services/growGuideService";

// Mock data for testing
const mockGrowGuideOptions: GrowGuideOptions = {
	lifecycles: [
		{
			lifecycle_id: "lifecycle-1",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		{
			lifecycle_id: "lifecycle-2",
			lifecycle_name: "Perennial",
			productivity_years: 5,
		},
		{
			lifecycle_id: "lifecycle-3",
			lifecycle_name: "Biennial",
			productivity_years: 2,
		},
	],
	planting_conditions: [
		{
			planting_condition_id: "condition-1",
			planting_condition: "Direct Sow",
		},
		{
			planting_condition_id: "condition-2",
			planting_condition: "Start Indoors",
		},
		{
			planting_condition_id: "condition-3",
			planting_condition: "Transplant",
		},
	],
	frequencies: [
		{
			frequency_id: "freq-1",
			frequency_name: "Daily",
			frequency_days_per_year: 365,
		},
		{
			frequency_id: "freq-2",
			frequency_name: "Weekly",
			frequency_days_per_year: 52,
		},
		{
			frequency_id: "freq-3",
			frequency_name: "Bi-weekly",
			frequency_days_per_year: 26,
		},
		{
			frequency_id: "freq-4",
			frequency_name: "Monthly",
			frequency_days_per_year: 12,
		},
	],
	feed_frequencies: [
		{
			frequency_id: "feed-freq-1",
			frequency_name: "Weekly",
			frequency_days_per_year: 52,
		},
		{
			frequency_id: "feed-freq-2",
			frequency_name: "Bi-weekly",
			frequency_days_per_year: 26,
		},
		{
			frequency_id: "feed-freq-3",
			frequency_name: "Monthly",
			frequency_days_per_year: 12,
		},
	],
	feeds: [
		{ feed_id: "feed-1", feed_name: "Compost" },
		{ feed_id: "feed-2", feed_name: "Liquid Fertilizer" },
		{ feed_id: "feed-3", feed_name: "Bone Meal" },
		{ feed_id: "feed-4", feed_name: "Tomato Feed" },
	],
	weeks: Array.from({ length: 52 }, (_, i) => ({
		week_id: `week-${i + 1}`,
		week_number: i + 1,
		week_start_date: new Date(2024, 0, i * 7 + 1).toISOString().split("T")[0],
		week_end_date: new Date(2024, 0, i * 7 + 7).toISOString().split("T")[0],
	})).map((w) => ({
		...w,
		week_label: `Week ${w.week_number.toString().padStart(2, "0")}`,
	})),
	families: [
		{ family_id: "family-1", family_name: "Brassicaceae" },
		{ family_id: "family-2", family_name: "Solanaceae" },
		{ family_id: "family-3", family_name: "Leguminosae" },
		{ family_id: "family-4", family_name: "Cucurbitaceae" },
		{ family_id: "family-5", family_name: "Allium" },
	],
	days: [
		{ day_id: "day-1", day_number: 1, day_name: "Monday" },
		{ day_id: "day-2", day_number: 2, day_name: "Tuesday" },
		{ day_id: "day-3", day_number: 3, day_name: "Wednesday" },
		{ day_id: "day-4", day_number: 4, day_name: "Thursday" },
		{ day_id: "day-5", day_number: 5, day_name: "Friday" },
		{ day_id: "day-6", day_number: 6, day_name: "Saturday" },
		{ day_id: "day-7", day_number: 7, day_name: "Sunday" },
	],
};

const mockUserGrowGuides: VarietyList[] = [
	{
		variety_id: "variety-1",
		variety_name: "Cherry Tomatoes",
		family: { family_id: "family-2", family_name: "Solanaceae" },
		lifecycle: {
			lifecycle_id: "lifecycle-1",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: false,
		last_updated: "2024-01-15T10:30:00Z",
	},
	{
		variety_id: "variety-2",
		variety_name: "Purple Sprouting Broccoli",
		family: { family_id: "family-1", family_name: "Brassicaceae" },
		lifecycle: {
			lifecycle_id: "lifecycle-3",
			lifecycle_name: "Biennial",
			productivity_years: 2,
		},
		is_public: true,
		last_updated: "2024-01-10T09:15:00Z",
	},
	{
		variety_id: "variety-3",
		variety_name: "Runner Beans",
		family: { family_id: "family-3", family_name: "Leguminosae" },
		lifecycle: {
			lifecycle_id: "lifecycle-1",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: false,
		last_updated: "2024-01-20T14:45:00Z",
	},
];

const mockPublicGrowGuides: VarietyList[] = [
	{
		variety_id: "public-variety-1",
		variety_name: "Heirloom Carrots",
		family: { family_id: "family-4", family_name: "Cucurbitaceae" },
		lifecycle: {
			lifecycle_id: "lifecycle-1",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: true,
		last_updated: "2024-01-05T08:00:00Z",
	},
	{
		variety_id: "public-variety-2",
		variety_name: "Spring Onions",
		family: { family_id: "family-5", family_name: "Allium" },
		lifecycle: {
			lifecycle_id: "lifecycle-1",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: true,
		last_updated: "2024-01-08T12:30:00Z",
	},
];

const createMockGrowGuideDetail = (
	varietyId: string,
	overrides: Partial<GrowGuideDetail> = {},
): GrowGuideDetail => {
	const baseGuide =
		mockUserGrowGuides.find((g) => g.variety_id === varietyId) ||
		mockUserGrowGuides[0];

	return {
		...baseGuide,
		owner_user_id: "user-123",
		soil_ph: 6.5,
		plant_depth_cm: 2.5,
		plant_space_cm: 30,
		row_width_cm: 45,
		high_temp_degrees: 25,
		notes: "Test notes for grow guide",
		sow_week_start_id: "week-10",
		sow_week_end_id: "week-20",
		transplant_week_start_id: "week-12",
		transplant_week_end_id: "week-22",
		harvest_week_start_id: "week-25",
		harvest_week_end_id: "week-35",
		prune_week_start_id: "week-15",
		prune_week_end_id: "week-30",
		planting_conditions: {
			planting_condition_id: "condition-2",
			planting_condition: "Start Indoors",
		},
		feed: { feed_id: "feed-2", feed_name: "Liquid Fertilizer" },
		feed_week_start_id: "week-15",
		feed_frequency: {
			frequency_id: "feed-freq-1",
			frequency_name: "Weekly",
			frequency_days_per_year: 52,
		},
		water_frequency: {
			frequency_id: "freq-2",
			frequency_name: "Weekly",
			frequency_days_per_year: 52,
		},
		high_temp_water_frequency: {
			frequency_id: "freq-1",
			frequency_name: "Daily",
			frequency_days_per_year: 365,
		},
		water_days: [
			{ day: { day_id: "day-1", day_number: 1, day_name: "Monday" } },
			{ day: { day_id: "day-3", day_number: 3, day_name: "Wednesday" } },
			{ day: { day_id: "day-5", day_number: 5, day_name: "Friday" } },
		],
		...overrides,
	};
};

// Store for tracking state across requests
let varietiesStore = [...mockUserGrowGuides];

export const growGuideHandlers = [
	// Get grow guide options
	http.get(buildUrl("/grow-guides/metadata"), ({ request }) => {
		const url = new URL(request.url);

		if (url.searchParams.get("error") === "500") {
			return jsonError("Internal server error", 500);
		}

		if (url.searchParams.get("error") === "network") {
			return HttpResponse.error();
		}

		return jsonOk(mockGrowGuideOptions);
	}),

	http.options(buildUrl("/grow-guides/metadata"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Get user grow guides
	http.get(buildUrl("/grow-guides"), ({ request }) => {
		const url = new URL(request.url);
		const visibility = url.searchParams.get("visibility");

		if (url.searchParams.get("error") === "500") {
			return jsonError("Internal server error", 500);
		}

		if (url.searchParams.get("error") === "network") {
			return HttpResponse.error();
		}

		if (url.searchParams.get("empty") === "true") {
			return jsonOk([]);
		}

		if (visibility === "public") {
			return jsonOk(mockPublicGrowGuides);
		}

		return jsonOk(varietiesStore);
	}),

	http.options(buildUrl("/grow-guides"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Create new grow guide
	http.post(buildUrl("/grow-guides"), async ({ request }) => {
		const body = await request.json();
		const data = body as {
			variety_name?: string;
			family_id?: string;
			lifecycle_id?: string;
			is_public?: boolean;
			[key: string]: unknown;
		};

		// Validation errors
		if (data.variety_name === "Duplicate Variety") {
			return jsonError("Variety already exists", 409);
		}

		if (data.variety_name === "Test Server Error") {
			return jsonError("Internal server error", 500);
		}

		if (
			!data.variety_name ||
			!data.family_id ||
			data.variety_name === "" ||
			data.family_id === ""
		) {
			return jsonError("Missing required fields", 422);
		}

		// Create new variety
		const newVariety: VarietyList = {
			variety_id: `variety-${Date.now()}`,
			variety_name: data.variety_name,
			family:
				mockGrowGuideOptions.families.find(
					(f) => f.family_id === data.family_id,
				) || mockGrowGuideOptions.families[0],
			lifecycle:
				mockGrowGuideOptions.lifecycles.find(
					(l) => l.lifecycle_id === data.lifecycle_id,
				) || mockGrowGuideOptions.lifecycles[0],
			is_public: data.is_public || false,
			last_updated: new Date().toISOString(),
		};

		varietiesStore.push(newVariety);

		const detailResponse = createMockGrowGuideDetail(newVariety.variety_id, {
			variety_id: newVariety.variety_id,
			variety_name: newVariety.variety_name,
			family: newVariety.family,
			lifecycle: newVariety.lifecycle,
			is_public: newVariety.is_public,
			last_updated: newVariety.last_updated,
		});

		return jsonOk(detailResponse);
	}),

	http.options(buildUrl("/grow-guides"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Get specific grow guide
	http.get(buildUrl("/grow-guides/:varietyId"), ({ params }) => {
		const { varietyId } = params;

		if (varietyId === "not-found") {
			return jsonError("Grow guide not found", 404);
		}

		if (varietyId === "server-error") {
			return jsonError("Internal server error", 500);
		}

		const mockDetail = createMockGrowGuideDetail(varietyId as string);
		return jsonOk(mockDetail);
	}),

	http.options(buildUrl("/grow-guides/:varietyId"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Update grow guide
	http.put(buildUrl("/grow-guides/:varietyId"), async ({ params, request }) => {
		const { varietyId } = params;
		const body = await request.json();
		const data = body as {
			variety_name?: string;
			is_public?: boolean;
			[key: string]: unknown;
		};

		if (varietyId === "not-found") {
			return jsonError("Grow guide not found", 404);
		}

		if (varietyId === "server-error") {
			return jsonError("Internal server error", 500);
		}

		if (varietyId === "variety-error") {
			return jsonError("Internal server error", 500);
		}

		if (data.variety_name === "invalid-update") {
			return jsonError("Invalid update data", 422);
		}

		// Update variety in store
		const index = varietiesStore.findIndex((v) => v.variety_id === varietyId);
		if (index >= 0) {
			varietiesStore[index] = {
				...varietiesStore[index],
				variety_name: data.variety_name || varietiesStore[index].variety_name,
				is_public:
					data.is_public !== undefined
						? data.is_public
						: varietiesStore[index].is_public,
				last_updated: new Date().toISOString(),
			};
		}

		const updatedDetail = createMockGrowGuideDetail(varietyId as string, {
			variety_name: data.variety_name,
			is_public: data.is_public,
			last_updated: new Date().toISOString(),
		});

		return jsonOk(updatedDetail);
	}),

	http.options(buildUrl("/grow-guides/:varietyId"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Delete grow guide
	http.delete(buildUrl("/grow-guides/:varietyId"), ({ params }) => {
		const { varietyId } = params;

		if (varietyId === "not-found") {
			return jsonError("Grow guide not found", 404);
		}

		if (varietyId === "server-error") {
			return jsonError("Internal server error", 500);
		}

		// Remove from store
		varietiesStore = varietiesStore.filter((v) => v.variety_id !== varietyId);

		return new HttpResponse(null, { status: 204 });
	}),

	http.options(buildUrl("/grow-guides/:varietyId"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Copy public variety to user's collection
	http.post(buildUrl("/grow-guides/:publicVarietyId/copy"), ({ params }) => {
		const { publicVarietyId } = params;

		if (publicVarietyId === "not-found") {
			return jsonError("Public grow guide not found", 404);
		}

		if (publicVarietyId === "server-error") {
			return jsonError("Internal server error", 500);
		}

		// Find public variety and create a copy
		const publicVariety = mockPublicGrowGuides.find(
			(v) => v.variety_id === publicVarietyId,
		);
		if (!publicVariety) {
			return jsonError("Public grow guide not found", 404);
		}

		const copiedVariety: VarietyList = {
			...publicVariety,
			variety_id: `variety-copy-${Date.now()}`,
			is_public: false,
			last_updated: new Date().toISOString(),
		};

		varietiesStore.push(copiedVariety);

		const detailResponse = createMockGrowGuideDetail(copiedVariety.variety_id, {
			variety_id: copiedVariety.variety_id,
			variety_name: copiedVariety.variety_name,
			family: copiedVariety.family,
			lifecycle: copiedVariety.lifecycle,
			is_public: copiedVariety.is_public,
			last_updated: copiedVariety.last_updated,
		});

		return jsonOk(detailResponse);
	}),

	http.options(buildUrl("/grow-guides/:publicVarietyId/copy"), () => {
		return new HttpResponse(null, { status: 204 });
	}),
];
