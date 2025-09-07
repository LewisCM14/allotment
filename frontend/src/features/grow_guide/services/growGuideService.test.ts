import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import {
	copyPublicVariety,
	createVariety,
	deleteVariety,
	getUserVarieties,
	getVarietyOptions,
	toggleVarietyPublic,
	updateVariety,
} from "./growGuideService";
import type {
	VarietyCreate,
	VarietyListRead,
	VarietyOptionsRead,
	VarietyRead,
	VarietyUpdate,
} from "../types/growGuideTypes";

describe("growGuideService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		localStorage.clear();
		vi.restoreAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("getVarietyOptions", () => {
		it("should get variety options successfully", async () => {
			const mockResponse: VarietyOptionsRead = {
				lifecycles: [
					{
						lifecycle_id: "lifecycle-1",
						lifecycle_name: "Annual",
						productivity_years: 1,
					},
				],
				planting_conditions: [
					{
						planting_condition_id: "condition-1",
						planting_condition: "Sunny",
					},
				],
				frequencies: [
					{
						frequency_id: "freq-1",
						frequency_name: "Weekly",
						frequency_days_per_year: 52,
					},
				],
				feeds: [
					{
						feed_id: "feed-1",
						feed_name: "Compost",
					},
				],
				weeks: [
					{
						week_id: "week-1",
						week_number: 1,
						week_start_date: "01/01",
						week_end_date: "07/01",
						start_month_id: "month-1",
					},
				],
				families: [
					{
						family_id: "family-1",
						family_name: "Brassica",
						botanical_group_id: "group-1",
					},
				],
			};

			server.use(
				http.get(buildUrl("/grow_guide/options"), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await getVarietyOptions();
			expect(result).toEqual(mockResponse);
		});

		it("should handle error when getting variety options", async () => {
			server.use(
				http.get(buildUrl("/grow_guide/options"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(getVarietyOptions()).rejects.toThrow();
		});
	});

	describe("getUserVarieties", () => {
		it("should get user varieties successfully", async () => {
			const mockResponse: VarietyListRead[] = [
				{
					variety_id: "variety-1",
					variety_name: "Tomato Beefsteak",
					lifecycle: {
						lifecycle_id: "lifecycle-1",
						lifecycle_name: "Annual",
						productivity_years: 1,
					},
					is_public: false,
					last_updated: "2024-01-01T00:00:00Z",
				},
			];

			server.use(
				http.get(buildUrl("/grow_guide"), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await getUserVarieties();
			expect(result).toEqual(mockResponse);
		});
	});

	describe("createVariety", () => {
		it("should create a variety successfully", async () => {
			const mockRequest: VarietyCreate = {
				variety_name: "Test Tomato",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency_id: "freq-1",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
			};

			const mockResponse: VarietyRead = {
				variety_id: "variety-1",
				variety_name: "Test Tomato",
				owner_user_id: "user-1",
				family: {
					family_id: "family-1",
					family_name: "Solanaceae",
					botanical_group_id: "group-1",
				},
				lifecycle: {
					lifecycle_id: "lifecycle-1",
					lifecycle_name: "Annual",
					productivity_years: 1,
				},
				planting_conditions: {
					planting_condition_id: "condition-1",
					planting_condition: "Sunny",
				},
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency: {
					frequency_id: "freq-1",
					frequency_name: "Weekly",
					frequency_days_per_year: 52,
				},
				high_temp_water_frequency: {
					frequency_id: "freq-2",
					frequency_name: "Daily",
					frequency_days_per_year: 365,
				},
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
				last_updated: "2024-01-01T00:00:00Z",
				water_days: [],
			};

			server.use(
				http.post(buildUrl("/grow_guide"), async ({ request }) => {
					const body = (await request.json()) as VarietyCreate;
					expect(body).toEqual(mockRequest);
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await createVariety(mockRequest);
			expect(result).toEqual(mockResponse);
		});
	});

	describe("updateVariety", () => {
		it("should update a variety successfully", async () => {
			const varietyId = "variety-1";
			const mockRequest: VarietyUpdate = {
				variety_name: "Updated Tomato",
				soil_ph: 7.0,
			};

			const mockResponse: VarietyRead = {
				variety_id: varietyId,
				variety_name: "Updated Tomato",
				owner_user_id: "user-1",
				family: {
					family_id: "family-1",
					family_name: "Solanaceae",
					botanical_group_id: "group-1",
				},
				lifecycle: {
					lifecycle_id: "lifecycle-1",
					lifecycle_name: "Annual",
					productivity_years: 1,
				},
				planting_conditions: {
					planting_condition_id: "condition-1",
					planting_condition: "Sunny",
				},
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				soil_ph: 7.0,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency: {
					frequency_id: "freq-1",
					frequency_name: "Weekly",
					frequency_days_per_year: 52,
				},
				high_temp_water_frequency: {
					frequency_id: "freq-2",
					frequency_name: "Daily",
					frequency_days_per_year: 365,
				},
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: false,
				last_updated: "2024-01-01T00:00:00Z",
				water_days: [],
			};

			server.use(
				http.put(buildUrl(`/grow_guide/${varietyId}`), async ({ request }) => {
					const body = (await request.json()) as VarietyUpdate;
					expect(body).toEqual(mockRequest);
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await updateVariety(varietyId, mockRequest);
			expect(result).toEqual(mockResponse);
		});
	});

	describe("deleteVariety", () => {
		it("should delete a variety successfully", async () => {
			const varietyId = "variety-1";

			server.use(
				http.delete(buildUrl(`/grow_guide/${varietyId}`), () => {
					return HttpResponse.json({}, { status: 204 });
				}),
			);

			await expect(
				deleteVariety(varietyId),
			).resolves.toBeUndefined();
		});
	});

	describe("toggleVarietyPublic", () => {
		it("should toggle variety public status successfully", async () => {
			const varietyId = "variety-1";

			const mockResponse: VarietyRead = {
				variety_id: varietyId,
				variety_name: "Test Tomato",
				owner_user_id: "user-1",
				family: {
					family_id: "family-1",
					family_name: "Solanaceae",
					botanical_group_id: "group-1",
				},
				lifecycle: {
					lifecycle_id: "lifecycle-1",
					lifecycle_name: "Annual",
					productivity_years: 1,
				},
				planting_conditions: {
					planting_condition_id: "condition-1",
					planting_condition: "Sunny",
				},
				sow_week_start_id: "week-1",
				sow_week_end_id: "week-2",
				soil_ph: 6.5,
				plant_depth_cm: 2,
				plant_space_cm: 30,
				water_frequency: {
					frequency_id: "freq-1",
					frequency_name: "Weekly",
					frequency_days_per_year: 52,
				},
				high_temp_water_frequency: {
					frequency_id: "freq-2",
					frequency_name: "Daily",
					frequency_days_per_year: 365,
				},
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				is_public: true,
				last_updated: "2024-01-01T00:00:00Z",
				water_days: [],
			};

			server.use(
				http.patch(buildUrl(`/grow_guide/${varietyId}/toggle-public`), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await toggleVarietyPublic(varietyId);
			expect(result).toEqual(mockResponse);
			expect(result.is_public).toBe(true);
		});
	});
});
