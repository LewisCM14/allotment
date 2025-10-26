import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { buildUrl } from "@/mocks/buildUrl";
import { todoService } from "./todoService";
import type { WeeklyTodoRead } from "../types/todoTypes";

const sampleWeekly: WeeklyTodoRead = {
	week_id: "week-20",
	week_number: 20,
	week_start_date: "15/05",
	week_end_date: "21/05",
	weekly_tasks: {
		sow_tasks: [
			{ variety_id: "v1", variety_name: "Radish", family_name: "Family" },
		],
		transplant_tasks: [],
		harvest_tasks: [],
		prune_tasks: [],
		compost_tasks: [],
	},
	daily_tasks: {},
};

describe("todoService", () => {
	it("getWeeklyTodo returns data for current week", async () => {
		server.use(
			http.get(buildUrl("/todos/weekly"), () =>
				HttpResponse.json(sampleWeekly),
			),
		);

		const data = await todoService.getWeeklyTodo();
		expect(data).toEqual(sampleWeekly);
	});

	it("getWeeklyTodo passes week_number param when provided", async () => {
		let capturedWeekParam: string | null = null;
		server.use(
			http.get(buildUrl("/todos/weekly"), ({ request }) => {
				const url = new URL(request.url);
				capturedWeekParam = url.searchParams.get("week_number");
				const weekNum = capturedWeekParam ? Number(capturedWeekParam) : 20;
				return HttpResponse.json({ ...sampleWeekly, week_number: weekNum });
			}),
		);

		const data = await todoService.getWeeklyTodo(19);
		expect(capturedWeekParam).toBe("19");
		expect(data.week_number).toBe(19);
	});

	it("getWeeklyTodo throws a friendly error on 500", async () => {
		server.use(
			http.get(buildUrl("/todos/weekly"), () =>
				HttpResponse.json({ detail: "Server error" }, { status: 500 }),
			),
		);

		await expect(todoService.getWeeklyTodo()).rejects.toThrow(
			/Server error\. Please try again later\./i,
		);
	});

	it("getWeeklyTodo throws a network error when request fails to reach server", async () => {
		server.use(http.get(buildUrl("/todos/weekly"), () => HttpResponse.error()));

		await expect(todoService.getWeeklyTodo()).rejects.toThrow(
			/Network error\. Please check your connection and try again\./i,
		);
	});

	it("getWeeklyTodo surfaces 404 detail string", async () => {
		server.use(
			http.get(buildUrl("/todos/weekly"), () =>
				HttpResponse.json({ detail: "no active varieties" }, { status: 404 }),
			),
		);

		await expect(todoService.getWeeklyTodo()).rejects.toThrow(
			/no active varieties/i,
		);
	});
});
