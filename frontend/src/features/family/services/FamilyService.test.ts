import axios from "axios";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import {
	FAMILY_SERVICE_ERRORS,
	type IBotanicalGroup,
	getBotanicalGroups,
} from "./FamilyService";

describe("FamilyService", () => {
	describe("getFamilyInfo", () => {
		it("should fetch family info successfully", async () => {
			const { getFamilyInfo } = await import("./FamilyService");
			const mockData = {
				id: "550e8400-e29b-41d4-a716-446655440008", // UUID format
				name: "Test Family",
				botanical_group: {
					id: "550e8400-e29b-41d4-a716-446655440009", // UUID format
					name: "BG",
					recommended_rotation_years: 2,
				},
				companion_to: [],
				antagonises: [],
				pests: [],
				diseases: [],
			};
			const getSpy = vi
				.spyOn(api, "get")
				.mockResolvedValueOnce({ data: mockData });
			const result = await getFamilyInfo(
				"550e8400-e29b-41d4-a716-446655440008",
			);
			expect(result).toEqual(mockData);
			getSpy.mockRestore();
		});

		it("should handle axios cancel error", async () => {
			const { getFamilyInfo } = await import("./FamilyService");
			const cancelError = new Error("canceled");
			Object.defineProperty(cancelError, "name", { value: "CanceledError" });
			const isCancelSpy = vi.spyOn(axios, "isCancel").mockReturnValue(true);
			const getSpy = vi.spyOn(api, "get").mockRejectedValueOnce(cancelError);
			await expect(
				getFamilyInfo("550e8400-e29b-41d4-a716-446655440010"),
			).rejects.toThrow("canceled");
			getSpy.mockRestore();
			isCancelSpy.mockRestore();
		});

		it("should handle unknown error", async () => {
			const { getFamilyInfo } = await import("./FamilyService");
			const genericError = new Error("Generic error");
			const getSpy = vi.spyOn(api, "get").mockRejectedValueOnce(genericError);
			await expect(
				getFamilyInfo("550e8400-e29b-41d4-a716-446655440011"),
			).rejects.toThrow();
			getSpy.mockRestore();
		});
	});

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
					id: "550e8400-e29b-41d4-a716-446655440000", // UUID format
					name: "Brassicaceae",
					recommended_rotation_years: 3,
					families: [
						{ id: "550e8400-e29b-41d4-a716-446655440001", name: "Cabbage" },
						{ id: "550e8400-e29b-41d4-a716-446655440002", name: "Broccoli" },
					],
				},
				{
					id: "550e8400-e29b-41d4-a716-446655440003", // UUID format
					name: "Solanaceae",
					recommended_rotation_years: 4,
					families: [
						{ id: "550e8400-e29b-41d4-a716-446655440004", name: "Tomatoes" },
						{ id: "550e8400-e29b-41d4-a716-446655440005", name: "Potatoes" },
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
			// Mock the get method to avoid retry logic in tests
			const getSpy = vi.spyOn(api, "get");
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
			// Mock the get method to avoid retry logic in tests
			const getSpy = vi.spyOn(api, "get");
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
			// Mock the get method to avoid retry logic in tests
			const getSpy = vi.spyOn(api, "get");
			const serverError = new Error("Server returned unexpected response");
			Object.defineProperty(serverError, "isAxiosError", { value: true });
			Object.defineProperty(serverError, "response", {
				value: {
					status: 502,
					data: "Bad Gateway",
				},
			});

			getSpy.mockRejectedValueOnce(serverError);

			await expect(getBotanicalGroups()).rejects.toThrow(
				FAMILY_SERVICE_ERRORS.FETCH_BOTANICAL_GROUPS_FAILED,
			);

			getSpy.mockRestore();
		});

		it("should handle abortion signal", async () => {
			const controller = new AbortController();
			const getSpy = vi.spyOn(api, "get");
			const isCancelSpy = vi.spyOn(axios, "isCancel");

			const cancelError = new Error("canceled");
			Object.defineProperty(cancelError, "name", { value: "CanceledError" });

			// Mock axios.isCancel to return true for cancellation
			isCancelSpy.mockReturnValue(true);

			getSpy.mockRejectedValueOnce(cancelError);
			controller.abort();

			await expect(getBotanicalGroups(controller.signal)).rejects.toThrow(
				"canceled",
			);

			getSpy.mockRestore();
			isCancelSpy.mockRestore();
		});

		it("should pass abort signal to API call", async () => {
			const controller = new AbortController();
			const getSpy = vi.spyOn(api, "get");
			getSpy.mockResolvedValueOnce({ data: [] });

			await getBotanicalGroups(controller.signal);

			expect(getSpy).toHaveBeenCalledWith(
				"/families/botanical-groups/",
				expect.objectContaining({
					signal: controller.signal,
				}),
			);

			getSpy.mockRestore();
		});

		it("should handle generic errors", async () => {
			const getSpy = vi.spyOn(api, "get");
			const genericError = new Error("Generic error");
			Object.defineProperty(genericError, "isAxiosError", { value: false });

			getSpy.mockRejectedValueOnce(genericError);

			await expect(getBotanicalGroups()).rejects.toThrow(
				FAMILY_SERVICE_ERRORS.FETCH_BOTANICAL_GROUPS_FAILED,
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
					id: "550e8400-e29b-41d4-a716-446655440006", // UUID format
					name: "Mixed Group",
					recommended_rotation_years: null,
					families: [
						{ id: "550e8400-e29b-41d4-a716-446655440007", name: "Herbs" },
					],
				},
			];

			const getSpy = vi.spyOn(api, "get");
			getSpy.mockResolvedValueOnce({ data: mockBotanicalGroups });

			const result = await getBotanicalGroups();

			expect(getSpy).toHaveBeenCalled();
			expect(result).not.toBeNull();
			expect(result?.[0].recommended_rotation_years).toBeNull();
			expect(result?.[0].name).toBe("Mixed Group");

			getSpy.mockRestore();
		});
	});
});
