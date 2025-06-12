import axios from "axios";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/handlers";
import { server } from "../../../mocks/server";
import * as apiModule from "../../../services/api";
import {
	FAMILY_SERVICE_ERRORS,
	type IBotanicalGroup,
	getBotanicalGroups,
} from "./FamilyService";

describe("FamilyService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		vi.restoreAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("getBotanicalGroups", () => {
		beforeEach(() => {
			server.use(
				http.options(buildUrl("/families/botanical-groups/"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
		});

		it("should fetch botanical groups successfully", async () => {
			const mockBotanicalGroups: IBotanicalGroup[] = [
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
			];

			server.use(
				http.get(buildUrl("/families/botanical-groups/"), () => {
					return HttpResponse.json(mockBotanicalGroups);
				}),
			);

			const result = await getBotanicalGroups();

			expect(result).not.toBeNull();
			expect(result).toEqual(mockBotanicalGroups);
			expect(result?.length).toBe(2);
			expect(result?.[0].families).toHaveLength(2);
		});

		it("should handle empty botanical groups response", async () => {
			server.use(
				http.get(buildUrl("/families/botanical-groups/"), () => {
					return HttpResponse.json([]);
				}),
			);

			const result = await getBotanicalGroups();

			expect(result).toEqual([]);
			expect(result).toHaveLength(0);
		});

		it("should handle server error (500)", async () => {
			const getSpy = vi.spyOn(apiModule.default, "get");
			const serverError = new Error("Server error");
			Object.defineProperty(serverError, "isAxiosError", { value: true });
			Object.defineProperty(serverError, "response", {
				value: {
					status: 500,
					data: { detail: "Internal Server Error" },
				},
			});

			getSpy.mockRejectedValueOnce(serverError);

			await expect(getBotanicalGroups()).rejects.toThrow(
				FAMILY_SERVICE_ERRORS.SERVER_ERROR,
			);

			getSpy.mockRestore();
		});

		it("should handle other HTTP errors", async () => {
			server.use(
				http.get(buildUrl("/families/botanical-groups/"), () => {
					return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
				}),
				http.options(buildUrl("/families/botanical-groups/"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);

			await expect(getBotanicalGroups()).rejects.toThrow("Forbidden");
		});

		it("should handle network errors", async () => {
			const getSpy = vi.spyOn(apiModule.default, "get");
			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "request", { value: {} });
			Object.defineProperty(networkError, "response", { value: undefined });

			getSpy.mockRejectedValueOnce(networkError);

			await expect(getBotanicalGroups()).rejects.toThrow(
				FAMILY_SERVICE_ERRORS.NETWORK_ERROR,
			);

			getSpy.mockRestore();
		});

		it("should handle unexpected server responses", async () => {
			const getSpy = vi.spyOn(apiModule.default, "get");
			const serverError = new Error("Server returned unexpected response");
			Object.defineProperty(serverError, "isAxiosError", { value: true });
			Object.defineProperty(serverError, "response", {
				value: {
					status: 502,
					data: "Bad Gateway",
				},
			});

			getSpy.mockRejectedValueOnce(serverError);

			await expect(getBotanicalGroups()).rejects.toThrow("Bad Gateway");

			getSpy.mockRestore();
		});

		it("should handle abortion signal", async () => {
			const controller = new AbortController();
			const getSpy = vi.spyOn(apiModule.default, "get");
			const isCancelSpy = vi.spyOn(axios, "isCancel");

			const cancelError = new Error("Request cancelled");
			Object.defineProperty(cancelError, "name", { value: "CanceledError" });

			// Mock axios.isCancel to return true for cancellation
			isCancelSpy.mockReturnValue(true);

			getSpy.mockRejectedValueOnce(cancelError);
			controller.abort();

			await expect(getBotanicalGroups(controller.signal)).rejects.toThrow(
				"Request cancelled",
			);

			getSpy.mockRestore();
			isCancelSpy.mockRestore();
		});

		it("should pass abort signal to API call", async () => {
			const controller = new AbortController();
			const getSpy = vi.spyOn(apiModule.default, "get");
			getSpy.mockResolvedValueOnce({ data: [] });

			await getBotanicalGroups(controller.signal);

			expect(getSpy).toHaveBeenCalledWith(
				expect.stringContaining("/families/botanical-groups/"),
				expect.objectContaining({
					signal: controller.signal,
				}),
			);

			getSpy.mockRestore();
		});

		it("should handle generic errors", async () => {
			const getSpy = vi.spyOn(apiModule.default, "get");
			const genericError = new Error("Generic error");
			Object.defineProperty(genericError, "isAxiosError", { value: false });

			getSpy.mockRejectedValueOnce(genericError);

			await expect(getBotanicalGroups()).rejects.toThrow(
				FAMILY_SERVICE_ERRORS.UNKNOWN_ERROR,
			);

			getSpy.mockRestore();
		});

		it("should handle malformed response data", async () => {
			server.use(
				http.get(buildUrl("/families/botanical-groups/"), () => {
					return HttpResponse.json(null);
				}),
			);

			const result = await getBotanicalGroups();
			expect(result).toEqual([]);
		});

		it("should handle botanical group with null rotation years", async () => {
			const mockBotanicalGroups: IBotanicalGroup[] = [
				{
					id: "group-1",
					name: "Mixed Group",
					recommended_rotation_years: null,
					families: [{ id: "family-1", name: "Herbs" }],
				},
			];

			const getSpy = vi.spyOn(apiModule.default, "get");
			getSpy.mockResolvedValueOnce({ data: mockBotanicalGroups });

			const result = await getBotanicalGroups();

			expect(getSpy).toHaveBeenCalled();
			expect(result).not.toBeNull();
			expect(result?.[0].recommended_rotation_years).toBeNull();
			expect(result?.[0].name).toBe("Mixed Group");

			getSpy.mockRestore();
		});
	});

	describe("getFamilyDetails", () => {
		beforeEach(() => {
			server.use(
				http.get(buildUrl("/families/:id"), ({ params }) => {
					const { id } = params;
					if (id === "family-1") {
						return HttpResponse.json({
							id: "family-1",
							name: "Cabbage",
							botanical_group: "Brassicaceae",
							recommended_rotation_years: 3,
							companion_families: ["Beans", "Peas"],
							antagonist_families: ["Tomatoes"],
							common_pests: ["Cabbage worm", "Aphids"],
							common_diseases: ["Clubroot", "Black rot"],
						});
					}
					if (id === "family-404") {
						return HttpResponse.json(
							{ detail: "Family not found" },
							{ status: 404 },
						);
					}
					if (id === "family-xyz") {
						return HttpResponse.json({
							id: "family-xyz",
							name: "Unknown Family",
						});
					}
					return HttpResponse.json(
						{ detail: "Unhandled mock" },
						{ status: 500 },
					);
				}),
				http.options(buildUrl("/families/:id"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
		});

		it("should fetch family details successfully", async () => {
			const { getFamilyDetails } = await import("./FamilyService");
			const result = await getFamilyDetails("family-1");
			expect(result).toMatchObject({
				id: "family-1",
				name: "Cabbage",
				botanical_group: "Brassicaceae",
				recommended_rotation_years: 3,
				companion_families: expect.arrayContaining(["Beans", "Peas"]),
				antagonist_families: expect.arrayContaining(["Tomatoes"]),
				common_pests: expect.any(Array),
				common_diseases: expect.any(Array),
			});
		});

		it("should handle not found error", async () => {
			const { getFamilyDetails } = await import("./FamilyService");
			await expect(getFamilyDetails("family-404")).rejects.toThrow(
				"Family not found",
			);
		});

		it("should handle unknown family gracefully", async () => {
			const { getFamilyDetails } = await import("./FamilyService");
			const result = await getFamilyDetails("family-xyz");
			expect(result).toMatchObject({
				id: "family-xyz",
				name: "Unknown Family",
			});
		});
	});
});
