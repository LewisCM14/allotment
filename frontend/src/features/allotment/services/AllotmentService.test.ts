import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import {
	createUserAllotment,
	getUserAllotment,
	updateUserAllotment,
	NoAllotmentFoundError,
	type IAllotmentRequest,
	type IAllotmentUpdateRequest,
	type IAllotmentResponse,
} from "./AllotmentService";

describe("UserAllotmentService", () => {
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

	describe("createUserAllotment", () => {
		it("should create a user allotment successfully", async () => {
			const mockRequest: IAllotmentRequest = {
				allotment_postal_zip_code: "A1A 1A1",
				allotment_width_meters: 10,
				allotment_length_meters: 20,
			};

			const mockResponse: IAllotmentResponse = {
				user_allotment_id: "123e4567-e89b-12d3-a456-426614174000",
				user_id: "456e7890-e89b-12d3-a456-426614174001",
				allotment_postal_zip_code: "A1A 1A1",
				allotment_width_meters: 10,
				allotment_length_meters: 20,
			};

			server.use(
				http.post(buildUrl("/users/allotment"), async ({ request }) => {
					const body = (await request.json()) as IAllotmentRequest;
					expect(body).toEqual(mockRequest);
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await createUserAllotment(mockRequest);
			expect(result).toEqual(mockResponse);
		});

		it("should handle validation errors (422)", async () => {
			const mockRequest: IAllotmentRequest = {
				allotment_postal_zip_code: "",
				allotment_width_meters: -1,
				allotment_length_meters: 0,
			};

			server.use(
				http.post(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{
							detail: [
								{
									loc: ["body", "allotment_postal_zip_code"],
									msg: "String should have at least 5 characters",
									type: "string_too_short",
								},
								{
									loc: ["body", "allotment_width_meters"],
									msg: "Input should be greater than or equal to 1",
									type: "greater_than_equal",
								},
							],
						},
						{ status: 422 },
					);
				}),
			);

			await expect(createUserAllotment(mockRequest)).rejects.toThrow(
				"String should have at least 5 characters",
			);
		});

		it("should handle server errors (500)", async () => {
			const mockRequest: IAllotmentRequest = {
				allotment_postal_zip_code: "A1A 1A1",
				allotment_width_meters: 10,
				allotment_length_meters: 20,
			};

			server.use(
				http.post(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(createUserAllotment(mockRequest)).rejects.toThrow(
				"Server error. Please try again later.",
			);
		});

		it("should handle network errors", async () => {
			const mockRequest: IAllotmentRequest = {
				allotment_postal_zip_code: "A1A 1A1",
				allotment_width_meters: 10,
				allotment_length_meters: 20,
			};

			// Mock network unavailable
			Object.defineProperty(navigator, "onLine", {
				value: false,
				writable: true,
			});

			server.use(
				http.post(buildUrl("/users/allotment"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(createUserAllotment(mockRequest)).rejects.toThrow();
		});
	});

	describe("getUserAllotment", () => {
		it("should fetch user allotment successfully", async () => {
			const mockResponse: IAllotmentResponse = {
				user_allotment_id: "123e4567-e89b-12d3-a456-426614174000",
				user_id: "456e7890-e89b-12d3-a456-426614174001",
				allotment_postal_zip_code: "B2B 2B2",
				allotment_width_meters: 15,
				allotment_length_meters: 25,
			};

			server.use(
				http.get(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await getUserAllotment();
			expect(result).toEqual(mockResponse);
		});

		it("should throw NoAllotmentFoundError for 404", async () => {
			server.use(
				http.get(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "User allotment not found." },
						{ status: 404 },
					);
				}),
			);

			await expect(getUserAllotment()).rejects.toThrow(NoAllotmentFoundError);
			await expect(getUserAllotment()).rejects.toThrow(
				"No allotment found for this user",
			);
		});

		it("should handle authentication errors (401)", async () => {
			server.use(
				http.get(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "Not authenticated" },
						{ status: 401 },
					);
				}),
			);

			await expect(getUserAllotment()).rejects.toThrow(
				"Invalid email or password. Please try again.",
			);
		});

		it("should handle server errors (500)", async () => {
			server.use(
				http.get(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(getUserAllotment()).rejects.toThrow(
				"Server error. Please try again later.",
			);
		});

		it("should handle network errors", async () => {
			// Mock network unavailable
			Object.defineProperty(navigator, "onLine", {
				value: false,
				writable: true,
			});

			server.use(
				http.get(buildUrl("/users/allotment"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(getUserAllotment()).rejects.toThrow();
		});
	});

	describe("updateUserAllotment", () => {
		it("should update user allotment successfully", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_postal_zip_code: "C3C 3C3",
				allotment_width_meters: 12,
			};

			const mockResponse: IAllotmentResponse = {
				user_allotment_id: "123e4567-e89b-12d3-a456-426614174000",
				user_id: "456e7890-e89b-12d3-a456-426614174001",
				allotment_postal_zip_code: "C3C 3C3",
				allotment_width_meters: 12,
				allotment_length_meters: 20, // Unchanged
			};

			server.use(
				http.put(buildUrl("/users/allotment"), async ({ request }) => {
					const body = (await request.json()) as IAllotmentUpdateRequest;
					expect(body).toEqual(mockRequest);
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await updateUserAllotment(mockRequest);
			expect(result).toEqual(mockResponse);
		});

		it("should update with partial data", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_width_meters: 8,
			};

			const mockResponse: IAllotmentResponse = {
				user_allotment_id: "123e4567-e89b-12d3-a456-426614174000",
				user_id: "456e7890-e89b-12d3-a456-426614174001",
				allotment_postal_zip_code: "A1A 1A1", // Unchanged
				allotment_width_meters: 8,
				allotment_length_meters: 20, // Unchanged
			};

			server.use(
				http.put(buildUrl("/users/allotment"), async ({ request }) => {
					const body = (await request.json()) as IAllotmentUpdateRequest;
					expect(body).toEqual(mockRequest);
					return HttpResponse.json(mockResponse);
				}),
			);

			const result = await updateUserAllotment(mockRequest);
			expect(result).toEqual(mockResponse);
		});

		it("should handle validation errors (422)", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_width_meters: -5,
			};

			server.use(
				http.put(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{
							detail: [
								{
									loc: ["body", "allotment_width_meters"],
									msg: "Input should be greater than or equal to 1",
									type: "greater_than_equal",
								},
							],
						},
						{ status: 422 },
					);
				}),
			);

			await expect(updateUserAllotment(mockRequest)).rejects.toThrow(
				"Input should be greater than or equal to 1",
			);
		});

		it("should handle not found errors (404)", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_postal_zip_code: "D4D 4D4",
			};

			server.use(
				http.put(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "User allotment not found." },
						{ status: 404 },
					);
				}),
			);

			await expect(updateUserAllotment(mockRequest)).rejects.toThrow(
				"User allotment not found.",
			);
		});

		it("should handle authentication errors (401)", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_postal_zip_code: "D4D 4D4",
			};

			server.use(
				http.put(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "Not authenticated" },
						{ status: 401 },
					);
				}),
			);

			await expect(updateUserAllotment(mockRequest)).rejects.toThrow(
				"Invalid email or password. Please try again.",
			);
		});

		it("should handle server errors (500)", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_postal_zip_code: "D4D 4D4",
			};

			server.use(
				http.put(buildUrl("/users/allotment"), () => {
					return HttpResponse.json(
						{ detail: "Internal server error" },
						{ status: 500 },
					);
				}),
			);

			await expect(updateUserAllotment(mockRequest)).rejects.toThrow(
				"Server error. Please try again later.",
			);
		});

		it("should handle network errors", async () => {
			const mockRequest: IAllotmentUpdateRequest = {
				allotment_postal_zip_code: "D4D 4D4",
			};

			// Mock network unavailable
			Object.defineProperty(navigator, "onLine", {
				value: false,
				writable: true,
			});

			server.use(
				http.put(buildUrl("/users/allotment"), () => {
					return HttpResponse.error();
				}),
			);

			await expect(updateUserAllotment(mockRequest)).rejects.toThrow();
		});
	});
});
