import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import { growGuideService } from "./growGuideService";
import type { VarietyCreate } from "../types/growGuideTypes";

describe("growGuideService", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("getUserGrowGuides", () => {
		it("should fetch user grow guides successfully", async () => {
			const result = await growGuideService.getUserGrowGuides();

			expect(Array.isArray(result)).toBe(true);
			expect(result.length).toBeGreaterThan(0);

			// Check structure of first item
			if (result.length > 0) {
				const guide = result[0];
				expect(guide).toHaveProperty("variety_id");
				expect(guide).toHaveProperty("variety_name");
				expect(guide).toHaveProperty("family");
				expect(guide).toHaveProperty("lifecycle");
				expect(guide).toHaveProperty("is_public");
				expect(guide).toHaveProperty("last_updated");
			}
		});

		it("should handle server error (500)", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(growGuideService.getUserGrowGuides()).rejects.toThrow();
		});

		it("should handle network errors", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(growGuideService.getUserGrowGuides()).rejects.toThrow();
		});

		it("should handle empty response", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return HttpResponse.json([]);
				}),
			);

			const result = await growGuideService.getUserGrowGuides();
			expect(result).toEqual([]);
		});
	});

	describe("getPublicGrowGuides", () => {
		it("should fetch public grow guides successfully", async () => {
			const result = await growGuideService.getPublicGrowGuides();

			expect(Array.isArray(result)).toBe(true);

			// Verify structure if results exist
			if (result.length > 0) {
				const guide = result[0];
				expect(guide).toHaveProperty("variety_id");
				expect(guide).toHaveProperty("variety_name");
				expect(guide).toHaveProperty("is_public");
				expect(guide.is_public).toBe(true);
			}
		});

		it("should handle error responses", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), ({ request }) => {
					const url = new URL(request.url);
					const visibility = url.searchParams.get("visibility");
					if (visibility === "public") {
						return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
					}
					return HttpResponse.json([]);
				}),
			);

			await expect(growGuideService.getPublicGrowGuides()).rejects.toThrow();
		});
	});

	describe("createGrowGuide", () => {
		it("should create a new grow guide successfully", async () => {
			const inputData: VarietyCreate = {
				variety_name: "Test Variety",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-8",
				sow_week_end_id: "week-12",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2.5,
				plant_space_cm: 30,
				water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
				transplant_week_start_id: "week-10",
				transplant_week_end_id: "week-14",
				feed_id: "feed-1",
				feed_week_start_id: "week-10",
				feed_frequency_id: "freq-1",
				high_temp_degrees: 25,
				high_temp_water_frequency_id: "freq-3",
				prune_week_start_id: "week-15",
				prune_week_end_id: "week-25",
				notes: "Test notes",
				is_public: false,
			};

			const result = await growGuideService.createGrowGuide(inputData);

			expect(result).toHaveProperty("variety_id");
			expect(result).toHaveProperty("variety_name", inputData.variety_name);
			expect(result).toHaveProperty("family");
			expect(result).toHaveProperty("lifecycle");
			expect(result).toHaveProperty("is_public", inputData.is_public);
			expect(result).toHaveProperty("last_updated");
		});

		it("should handle validation errors (409)", async () => {
			const inputData: VarietyCreate = {
				variety_name: "Duplicate Variety",
				family_id: "family-1",
				lifecycle_id: "lifecycle-1",
				sow_week_start_id: "week-8",
				sow_week_end_id: "week-12",
				planting_conditions_id: "condition-1",
				soil_ph: 6.5,
				plant_depth_cm: 2.5,
				plant_space_cm: 30,
				water_frequency_id: "freq-2",
				harvest_week_start_id: "week-20",
				harvest_week_end_id: "week-30",
			};

			await expect(
				growGuideService.createGrowGuide(inputData),
			).rejects.toThrow();
		});

		it("should handle missing required fields (422)", async () => {
			const inputData = {
				variety_name: "",
				family_id: "",
			} as unknown as VarietyCreate;

			await expect(
				growGuideService.createGrowGuide(inputData),
			).rejects.toThrow();
		});
	});

	describe("getGrowGuideOptions", () => {
		it("should fetch grow guide options successfully", async () => {
			const result = await growGuideService.getGrowGuideOptions();

			expect(result).toHaveProperty("lifecycles");
			expect(result).toHaveProperty("families");
			expect(result).toHaveProperty("planting_conditions");
			expect(result).toHaveProperty("feeds");
			expect(result).toHaveProperty("frequencies");
			expect(result).toHaveProperty("days");
			expect(result).toHaveProperty("weeks");

			expect(Array.isArray(result.lifecycles)).toBe(true);
			expect(Array.isArray(result.families)).toBe(true);
			expect(Array.isArray(result.planting_conditions)).toBe(true);
			expect(Array.isArray(result.feeds)).toBe(true);
			expect(Array.isArray(result.frequencies)).toBe(true);
			expect(Array.isArray(result.days)).toBe(true);
			expect(Array.isArray(result.weeks)).toBe(true);
		});

		it("should handle server errors", async () => {
			server.use(
				http.get(buildUrl("/grow-guides/metadata"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(growGuideService.getGrowGuideOptions()).rejects.toThrow();
		});
	});

	describe("getGrowGuide", () => {
		it("should fetch specific grow guide successfully", async () => {
			const varietyId = "variety-1";

			const result = await growGuideService.getGrowGuide(varietyId);

			expect(result).toHaveProperty("variety_id");
			expect(result).toHaveProperty("variety_name");
			expect(result).toHaveProperty("family");
			expect(result).toHaveProperty("lifecycle");
			expect(result).toHaveProperty("soil_ph");
			expect(result).toHaveProperty("plant_depth_cm");
			expect(result).toHaveProperty("plant_space_cm");
			expect(result).toHaveProperty("planting_conditions");
			expect(result).toHaveProperty("feed");
			expect(result).toHaveProperty("feed_frequency");
			expect(result).toHaveProperty("water_frequency");
			expect(result).toHaveProperty("water_days");
			expect(result).toHaveProperty("is_public");
			expect(result).toHaveProperty("last_updated");
		});

		it("should handle grow guide not found (404)", async () => {
			const varietyId = "not-found";

			await expect(growGuideService.getGrowGuide(varietyId)).rejects.toThrow();
		});
	});

	describe("updateVariety", () => {
		it("should update grow guide successfully", async () => {
			const varietyId = "variety-1";
			const updateData = { variety_name: "Updated Variety Name" };

			const result = await growGuideService.updateVariety(
				varietyId,
				updateData,
			);

			expect(result).toHaveProperty("variety_id", varietyId);
			expect(result).toHaveProperty("variety_name", updateData.variety_name);
			expect(result).toHaveProperty("last_updated");
		});

		it("should handle update validation errors", async () => {
			const varietyId = "variety-1";
			const updateData = { variety_name: "invalid-update" };

			await expect(
				growGuideService.updateVariety(varietyId, updateData),
			).rejects.toThrow();
		});

		it("should handle variety not found", async () => {
			const varietyId = "not-found";
			const updateData = { variety_name: "Updated Name" };

			await expect(
				growGuideService.updateVariety(varietyId, updateData),
			).rejects.toThrow();
		});
	});

	describe("deleteVariety", () => {
		it("should delete grow guide successfully", async () => {
			const varietyId = "variety-1";

			const result = await growGuideService.deleteVariety(varietyId);

			expect(result).toBeUndefined();
		});

		it("should handle delete errors", async () => {
			const varietyId = "not-found";

			await expect(growGuideService.deleteVariety(varietyId)).rejects.toThrow();
		});
	});

	describe("toggleVarietyPublic", () => {
		it("should toggle variety public status successfully", async () => {
			const varietyId = "variety-1";
			const currentIsPublic = false;

			const result = await growGuideService.toggleVarietyPublic(
				varietyId,
				currentIsPublic,
			);

			expect(result).toHaveProperty("variety_id", varietyId);
			expect(result).toHaveProperty("is_public", true);
			expect(result).toHaveProperty("last_updated");
		});

		it("should handle toggle errors", async () => {
			const varietyId = "variety-error";
			const currentIsPublic = false;

			await expect(
				growGuideService.toggleVarietyPublic(varietyId, currentIsPublic),
			).rejects.toThrow();
		});

		it("should handle variety not found", async () => {
			const varietyId = "not-found";
			const currentIsPublic = false;

			await expect(
				growGuideService.toggleVarietyPublic(varietyId, currentIsPublic),
			).rejects.toThrow();
		});
	});

	describe("copyPublicVariety", () => {
		it("should copy public variety successfully", async () => {
			const varietyId = "public-variety-1";

			const result = await growGuideService.copyPublicVariety(varietyId);

			expect(result).toHaveProperty("variety_id");
			expect(result).toHaveProperty("variety_name");
			expect(result).toHaveProperty("family");
			expect(result).toHaveProperty("lifecycle");
			expect(result).toHaveProperty("is_public", false); // Copied varieties are private
			expect(result).toHaveProperty("last_updated");
		});

		it("should handle copy errors when public variety not found", async () => {
			const varietyId = "not-found";

			await expect(
				growGuideService.copyPublicVariety(varietyId),
			).rejects.toThrow();
		});

		it("should handle server errors during copy", async () => {
			const varietyId = "server-error";

			await expect(
				growGuideService.copyPublicVariety(varietyId),
			).rejects.toThrow();
		});
	});
});
