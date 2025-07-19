import { HttpResponse, type JsonBodyType } from "msw";

export const jsonOk = (data: JsonBodyType) => HttpResponse.json(data);

export const jsonError = (detail: string, status = 400) =>
	new HttpResponse(JSON.stringify({ detail }), {
		status,
		headers: { "Content-Type": "application/json" },
	});
