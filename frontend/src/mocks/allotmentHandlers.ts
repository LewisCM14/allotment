import { http, HttpResponse } from "msw";
import { buildUrl } from "./buildUrl";
import { jsonOk } from "./responseHelpers";

interface IAllotmentRequest {
	allotment_postal_zip_code: string;
	allotment_width_meters: number;
	allotment_length_meters: number;
}

interface IAllotmentResponse {
	user_allotment_id: string;
	user_id: string;
	allotment_postal_zip_code: string;
	allotment_width_meters: number;
	allotment_length_meters: number;
}

export const allotmentHandlers = [
	// Mock create user allotment
	http.post(buildUrl("/users/allotment"), async ({ request }) => {
		const body = (await request.json()) as IAllotmentRequest;

		return jsonOk({
			user_allotment_id: "allotment-123",
			user_id: "user-123",
			allotment_postal_zip_code: body.allotment_postal_zip_code,
			allotment_width_meters: body.allotment_width_meters,
			allotment_length_meters: body.allotment_length_meters,
		} as IAllotmentResponse);
	}),
	http.options(buildUrl("/users/allotment"), () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Mock get user allotment
	http.get(buildUrl("/users/allotment"), () => {
		return jsonOk({
			user_allotment_id: "allotment-123",
			user_id: "user-123",
			allotment_postal_zip_code: "12345",
			allotment_width_meters: 10.5,
			allotment_length_meters: 15.0,
		} as IAllotmentResponse);
	}),

	// Mock update user allotment
	http.put(buildUrl("/users/allotment"), async ({ request }) => {
		const body = (await request.json()) as Partial<IAllotmentRequest>;

		return jsonOk({
			user_allotment_id: "allotment-123",
			user_id: "user-123",
			allotment_postal_zip_code: body.allotment_postal_zip_code ?? "12345",
			allotment_width_meters: body.allotment_width_meters ?? 10.5,
			allotment_length_meters: body.allotment_length_meters ?? 15.0,
		} as IAllotmentResponse);
	}),
];
