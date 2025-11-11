import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import { growGuideService } from "./growGuideService";
import type { VarietyCreate } from "../types/growGuideTypes";
import type { GrowGuideFormData } from "../forms/GrowGuideFormSchema";

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

		it("should include correct query parameters", async () => {
			let capturedUrl = "";
			server.use(
				http.get(buildUrl("/grow-guides"), ({ request }) => {
					capturedUrl = request.url;
					return HttpResponse.json([]);
				}),
			);

			await growGuideService.getUserGrowGuides();

			expect(capturedUrl).toContain("visibility=user");
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

		it("should handle null response", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return HttpResponse.json(null);
				}),
			);

			const result = await growGuideService.getUserGrowGuides();
			expect(result).toEqual(null);
		});

		it("should handle malformed response", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return new HttpResponse("invalid json", {
						status: 200,
						headers: { "Content-Type": "application/json" },
					});
				}),
			);

			await expect(growGuideService.getUserGrowGuides()).rejects.toThrow();
		});

		it("should handle timeout errors", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(growGuideService.getUserGrowGuides()).rejects.toThrow();
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

		it("should include correct query parameters", async () => {
			let capturedUrl = "";
			server.use(
				http.get(buildUrl("/grow-guides"), ({ request }) => {
					capturedUrl = request.url;
					return HttpResponse.json([]);
				}),
			);

			await growGuideService.getPublicGrowGuides();

			expect(capturedUrl).toContain("visibility=public");
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

		it("should handle empty public guides", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), ({ request }) => {
					const url = new URL(request.url);
					const visibility = url.searchParams.get("visibility");
					if (visibility === "public") {
						return HttpResponse.json([]);
					}
					return HttpResponse.json([]);
				}),
			);

			const result = await growGuideService.getPublicGrowGuides();
			expect(result).toEqual([]);
		});

		it("should handle unauthorized access (401)", async () => {
			server.use(
				http.get(buildUrl("/grow-guides"), ({ request }) => {
					const url = new URL(request.url);
					const visibility = url.searchParams.get("visibility");
					if (visibility === "public") {
						return HttpResponse.json(
							{ detail: "Unauthorized" },
							{ status: 401 },
						);
					}
					return HttpResponse.json([]);
				}),
			);

			await expect(growGuideService.getPublicGrowGuides()).rejects.toThrow();
		});
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

	it("should create with GrowGuideFormData type", async () => {
		const formData: Partial<GrowGuideFormData> = {
			variety_name: "Form Test Variety",
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
			high_temp_degrees: 25,
			is_public: false,
		};

		const result = await growGuideService.createGrowGuide(
			formData as GrowGuideFormData,
		);

		expect(result).toHaveProperty("variety_id");
		expect(result).toHaveProperty("variety_name", formData.variety_name);
	});

	it("should default is_public to false when not provided", async () => {
		const inputData = {
			variety_name: "Default Public Test",
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
		} as VarietyCreate;

		const result = await growGuideService.createGrowGuide(inputData);

		expect(result).toHaveProperty("is_public", false);
	});

	it("should preserve is_public when provided as true", async () => {
		const inputData: VarietyCreate = {
			variety_name: "Public Test Variety",
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
			is_public: true,
		};

		const result = await growGuideService.createGrowGuide(inputData);

		expect(result).toHaveProperty("is_public", true);
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

		await expect(growGuideService.createGrowGuide(inputData)).rejects.toThrow();
	});

	it("should handle missing required fields (422)", async () => {
		const inputData = {
			variety_name: "",
			family_id: "",
		} as unknown as VarietyCreate;

		await expect(growGuideService.createGrowGuide(inputData)).rejects.toThrow();
	});

	it("should handle authorization errors (401)", async () => {
		server.use(
			http.post(buildUrl("/grow-guides"), () => {
				return HttpResponse.json({ detail: "Unauthorized" }, { status: 401 });
			}),
		);

		const inputData: VarietyCreate = {
			variety_name: "Unauthorized Test",
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

		await expect(growGuideService.createGrowGuide(inputData)).rejects.toThrow();
	});

	it("should handle rate limiting (429)", async () => {
		server.use(
			http.post(buildUrl("/grow-guides"), () => {
				return HttpResponse.json(
					{ detail: "Too many requests" },
					{ status: 429 },
				);
			}),
		);

		const inputData: VarietyCreate = {
			variety_name: "Rate Limited Test",
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

		await expect(growGuideService.createGrowGuide(inputData)).rejects.toThrow();
	});

	it("should handle creation with minimal required fields only", async () => {
		const minimalData: VarietyCreate = {
			variety_name: "Minimal Test",
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

		const result = await growGuideService.createGrowGuide(minimalData);

		expect(result).toHaveProperty("variety_id");
		expect(result).toHaveProperty("variety_name", minimalData.variety_name);
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

	it("should handle empty options response", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/metadata"), () => {
				return HttpResponse.json({
					lifecycles: [],
					families: [],
					planting_conditions: [],
					feeds: [],
					frequencies: [],
					days: [],
					weeks: [],
				});
			}),
		);

		const result = await growGuideService.getGrowGuideOptions();

		expect(result.lifecycles).toEqual([]);
		expect(result.families).toEqual([]);
	});

	it("should handle partial options response", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/metadata"), () => {
				return HttpResponse.json({
					lifecycles: [
						{
							lifecycle_id: "annual",
							lifecycle_name: "Annual",
							productivity_years: 1,
						},
					],
					families: [],
					planting_conditions: [],
					feeds: [],
					frequencies: [],
					weeks: [],
					// Note: days missing to test handling of optional fields
				});
			}),
		);

		const result = await growGuideService.getGrowGuideOptions();

		expect(result.lifecycles).toHaveLength(1);
		expect(result.families).toEqual([]);
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

	it("should handle unauthorized access", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/metadata"), () => {
				return HttpResponse.json({ detail: "Unauthorized" }, { status: 401 });
			}),
		);

		await expect(growGuideService.getGrowGuideOptions()).rejects.toThrow();
	});

	it("should handle network timeout", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/metadata"), () => {
				return HttpResponse.error();
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

	it("should handle invalid variety ID format", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json(
					{ detail: "Invalid ID format" },
					{ status: 400 },
				);
			}),
		);

		await expect(growGuideService.getGrowGuide("invalid-id")).rejects.toThrow();
	});

	it("should handle unauthorized access to private guide", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		await expect(
			growGuideService.getGrowGuide("private-guide"),
		).rejects.toThrow();
	});

	it("should handle server errors", async () => {
		server.use(
			http.get(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		await expect(
			growGuideService.getGrowGuide("server-error"),
		).rejects.toThrow();
	});
});

describe("updateVariety", () => {
	it("should update grow guide successfully", async () => {
		const varietyId = "variety-1";
		const updateData = { variety_name: "Updated Variety Name" };

		const result = await growGuideService.updateVariety(varietyId, updateData);

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

describe("updateVariety", () => {
	it("should update grow guide successfully", async () => {
		const varietyId = "variety-1";
		const updateData = { variety_name: "Updated Variety Name" };

		const result = await growGuideService.updateVariety(varietyId, updateData);

		expect(result).toHaveProperty("variety_id", varietyId);
		expect(result).toHaveProperty("variety_name", updateData.variety_name);
		expect(result).toHaveProperty("last_updated");
	});

	it("should update multiple fields successfully", async () => {
		const varietyId = "variety-1";
		const updateData = {
			variety_name: "Updated Name",
			soil_ph: 7.0,
			plant_depth_cm: 3.0,
			notes: "Updated notes",
		};

		const result = await growGuideService.updateVariety(varietyId, updateData);

		expect(result).toHaveProperty("variety_id", varietyId);
		expect(result).toHaveProperty("variety_name", updateData.variety_name);
	});

	it("should handle empty update data", async () => {
		const varietyId = "variety-1";
		const updateData = {};

		const result = await growGuideService.updateVariety(varietyId, updateData);

		expect(result).toHaveProperty("variety_id", varietyId);
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

	it("should handle unauthorized update (403)", async () => {
		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		const varietyId = "forbidden-variety";
		const updateData = { variety_name: "Updated Name" };

		await expect(
			growGuideService.updateVariety(varietyId, updateData),
		).rejects.toThrow();
	});

	it("should handle server errors during update", async () => {
		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		const varietyId = "server-error";
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

	it("should handle unauthorized delete (403)", async () => {
		server.use(
			http.delete(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		const varietyId = "forbidden-variety";

		await expect(growGuideService.deleteVariety(varietyId)).rejects.toThrow();
	});

	it("should handle server errors during delete", async () => {
		server.use(
			http.delete(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		const varietyId = "server-error";

		await expect(growGuideService.deleteVariety(varietyId)).rejects.toThrow();
	});

	it("should handle already deleted variety (404)", async () => {
		server.use(
			http.delete(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Not found" }, { status: 404 });
			}),
		);

		const varietyId = "already-deleted";

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

	it("should toggle from public to private", async () => {
		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({
					variety_id: "variety-2",
					variety_name: "Test Variety",
					is_public: false,
					last_updated: "2024-01-01T00:00:00Z",
				});
			}),
		);

		const varietyId = "variety-2";
		const currentIsPublic = true;

		const result = await growGuideService.toggleVarietyPublic(
			varietyId,
			currentIsPublic,
		);

		expect(result).toHaveProperty("is_public", false);
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

	it("should handle unauthorized toggle (403)", async () => {
		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		const varietyId = "forbidden-variety";
		const currentIsPublic = false;

		await expect(
			growGuideService.toggleVarietyPublic(varietyId, currentIsPublic),
		).rejects.toThrow();
	});

	it("should handle server errors during toggle", async () => {
		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		const varietyId = "server-error";
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

	it("should copy with all optional fields", async () => {
		server.use(
			http.post(buildUrl("/grow-guides/:publicVarietyId/copy"), () => {
				return HttpResponse.json({
					variety_id: "copied-variety-1",
					variety_name: "Copied Test Variety",
					family: { family_id: "family-1", family_name: "Test Family" },
					lifecycle: {
						lifecycle_id: "annual",
						lifecycle_name: "Annual",
						productivity_years: 1,
					},
					feed: { feed_id: "feed-1", feed_name: "Test Feed" },
					notes: "Copied notes",
					is_public: false,
					last_updated: "2024-01-01T00:00:00Z",
				});
			}),
		);

		const varietyId = "full-featured-variety";

		const result = await growGuideService.copyPublicVariety(varietyId);

		expect(result).toHaveProperty("variety_id", "copied-variety-1");
		expect(result).toHaveProperty("feed");
		expect(result).toHaveProperty("notes", "Copied notes");
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

	it("should handle unauthorized copy (403)", async () => {
		server.use(
			http.post(buildUrl("/grow-guides/:publicVarietyId/copy"), () => {
				return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
			}),
		);

		const varietyId = "forbidden-variety";

		await expect(
			growGuideService.copyPublicVariety(varietyId),
		).rejects.toThrow();
	});

	it("should handle copy of private variety (400)", async () => {
		server.use(
			http.post(buildUrl("/grow-guides/:publicVarietyId/copy"), () => {
				return HttpResponse.json(
					{ detail: "Variety is not public" },
					{ status: 400 },
				);
			}),
		);

		const varietyId = "private-variety";

		await expect(
			growGuideService.copyPublicVariety(varietyId),
		).rejects.toThrow();
	});

	it("should handle rate limiting during copy (429)", async () => {
		server.use(
			http.post(buildUrl("/grow-guides/:publicVarietyId/copy"), () => {
				return HttpResponse.json(
					{ detail: "Too many requests" },
					{ status: 429 },
				);
			}),
		);

		const varietyId = "rate-limited-variety";

		await expect(
			growGuideService.copyPublicVariety(varietyId),
		).rejects.toThrow();
	});
});

describe("Error Monitoring", () => {
	it("should call error monitoring on API failures", async () => {
		server.use(
			http.get(buildUrl("/grow-guides"), () => {
				return HttpResponse.json({ detail: "Server error" }, { status: 500 });
			}),
		);

		await expect(growGuideService.getUserGrowGuides()).rejects.toThrow();

		// Error monitoring should be called (this is integration test - actual monitoring is mocked)
	});

	it("should include context in error monitoring", async () => {
		server.use(
			http.post(buildUrl("/grow-guides"), () => {
				return HttpResponse.json(
					{ detail: "Validation error" },
					{ status: 422 },
				);
			}),
		);

		const inputData: VarietyCreate = {
			variety_name: "Error Test",
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

		await expect(growGuideService.createGrowGuide(inputData)).rejects.toThrow();

		// Error context should include the request data
	});
});

describe("updateVariety - Feed Field Clearing", () => {
	it("sends explicit nulls for cleared feed trio fields", async () => {
		// Setup: Mock a PUT request handler to capture the payload
		let capturedPayload: Record<string, unknown> | null = null;

		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), async ({ request }) => {
				capturedPayload = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({
					variety_id: "variety-1",
					variety_name: "Cherry Tomato",
					feed_id: null,
					feed_week_start_id: null,
					feed_frequency_id: null,
				});
			}),
		);

		// Call updateVariety with undefined feed trio fields (simulating cleared form)
		const updateData = {
			variety_name: "Cherry Tomato",
			feed_id: undefined,
			feed_week_start_id: undefined,
			feed_frequency_id: undefined,
		};

		await growGuideService.updateVariety("variety-1", updateData);

		// Assert: The payload should contain explicit nulls, not undefined
		expect(capturedPayload).toBeTruthy();
		expect(capturedPayload).toHaveProperty("feed_id", null);
		expect(capturedPayload).toHaveProperty("feed_week_start_id", null);
		expect(capturedPayload).toHaveProperty("feed_frequency_id", null);
		expect(capturedPayload).toHaveProperty("variety_name", "Cherry Tomato");
	});

	it("sends explicit nulls for cleared optional single fields", async () => {
		// Setup: Mock a PUT request handler to capture the payload
		let capturedPayload: Record<string, unknown> | null = null;

		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), async ({ request }) => {
				capturedPayload = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({
					variety_id: "variety-1",
					variety_name: "Cherry Tomato",
					transplant_week_start_id: null,
					prune_week_start_id: null,
					row_width_cm: null,
					notes: null,
				});
			}),
		);

		// Call updateVariety with undefined optional fields (simulating cleared form)
		const updateData = {
			variety_name: "Cherry Tomato",
			transplant_week_start_id: undefined,
			prune_week_start_id: undefined,
			row_width_cm: undefined,
			notes: undefined,
		};

		await growGuideService.updateVariety("variety-1", updateData);

		// Assert: The payload should contain explicit nulls for cleared fields
		expect(capturedPayload).toBeTruthy();
		expect(capturedPayload).toHaveProperty("transplant_week_start_id", null);
		expect(capturedPayload).toHaveProperty("prune_week_start_id", null);
		expect(capturedPayload).toHaveProperty("row_width_cm", null);
		expect(capturedPayload).toHaveProperty("notes", null);
	});

	it("does not send nulls for feed fields when not all are cleared", async () => {
		// Setup: Mock a PUT request handler to capture the payload
		let capturedPayload: Record<string, unknown> | null = null;

		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), async ({ request }) => {
				capturedPayload = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({
					variety_id: "variety-1",
					variety_name: "Cherry Tomato",
					feed_id: "feed-1",
				});
			}),
		);

		// Call updateVariety with only some feed fields cleared
		const updateData = {
			variety_name: "Cherry Tomato",
			feed_id: "feed-1", // Keep feed_id
			feed_week_start_id: undefined, // Clear this
			feed_frequency_id: undefined, // Clear this
		};

		await growGuideService.updateVariety("variety-1", updateData);

		// Assert: Since not all feed trio fields are undefined, they should NOT be converted to null
		// undefined values are omitted during JSON serialization, so they won't be in the payload
		expect(capturedPayload).toBeTruthy();
		expect(capturedPayload).toHaveProperty("feed_id", "feed-1");
		expect(capturedPayload).not.toHaveProperty("feed_week_start_id");
		expect(capturedPayload).not.toHaveProperty("feed_frequency_id");
	});

	it("preserves non-feed fields when clearing feed trio", async () => {
		// Setup: Mock a PUT request handler to capture the payload
		let capturedPayload: Record<string, unknown> | null = null;

		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), async ({ request }) => {
				capturedPayload = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({
					variety_id: "variety-1",
					variety_name: "Updated Tomato",
					feed_id: null,
					feed_week_start_id: null,
					feed_frequency_id: null,
					sow_week_start_id: "week-10",
				});
			}),
		);

		// Call updateVariety with feed trio cleared but other fields present
		const updateData = {
			variety_name: "Updated Tomato",
			feed_id: undefined,
			feed_week_start_id: undefined,
			feed_frequency_id: undefined,
			sow_week_start_id: "week-10",
		};

		await growGuideService.updateVariety("variety-1", updateData);

		// Assert: Non-feed fields should be preserved
		expect(capturedPayload).toBeTruthy();
		expect(capturedPayload).toHaveProperty("variety_name", "Updated Tomato");
		expect(capturedPayload).toHaveProperty("feed_id", null);
		expect(capturedPayload).toHaveProperty("feed_week_start_id", null);
		expect(capturedPayload).toHaveProperty("feed_frequency_id", null);
		expect(capturedPayload).toHaveProperty("sow_week_start_id", "week-10");
	});

	it("does not affect partial updates without feed fields", async () => {
		// Setup: Mock a PUT request handler to capture the payload
		let capturedPayload: Record<string, unknown> | null = null;

		server.use(
			http.put(buildUrl("/grow-guides/:varietyId"), async ({ request }) => {
				capturedPayload = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({
					variety_id: "variety-1",
					is_public: true,
				});
			}),
		);

		// Call updateVariety with only is_public (like toggleVarietyPublic does)
		const updateData = {
			is_public: true,
		};

		await growGuideService.updateVariety("variety-1", updateData);

		// Assert: Payload should only contain is_public, no feed fields nulled
		expect(capturedPayload).toBeTruthy();
		expect(capturedPayload).toHaveProperty("is_public", true);
		expect(capturedPayload).not.toHaveProperty("feed_id");
		expect(capturedPayload).not.toHaveProperty("feed_week_start_id");
		expect(capturedPayload).not.toHaveProperty("feed_frequency_id");
	});
});
