import { render, screen, waitFor } from "@testing-library/react";
import BotanicalGroupsPage from "./BotanicalGroups";
import * as BotanicalGroupsHook from "../hooks/useBotanicalGroups";
import React from "react";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock useBotanicalGroups
vi.mock("../hooks/useBotanicalGroups");

describe("BotanicalGroupsPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders loading state initially", async () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [],
				isLoading: true,
				error: null,
				isSuccess: false,
			},
		);
		render(
			<MemoryRouter>
				<BotanicalGroupsPage />
			</MemoryRouter>,
		);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("renders error state", async () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [],
				isLoading: false,
				error: new Error("Failed to fetch"),
				isSuccess: false,
			},
		);
		render(
			<MemoryRouter>
				<BotanicalGroupsPage />
			</MemoryRouter>,
		);
		expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
	});

	it("renders botanical groups with empty families", async () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [
					{
						botanical_group_id: 1,
						botanical_group_name: "Group 1",
						rotate_years: 2,
						families: [],
					},
				],
				isLoading: false,
				error: null,
				isSuccess: true,
			},
		);
		render(
			<MemoryRouter>
				<BotanicalGroupsPage />
			</MemoryRouter>,
		);
		expect(screen.getByText(/group 1/i)).toBeInTheDocument();
		// Open the accordion to reveal content
		const trigger = screen.getByRole("button", { name: /group 1/i });
		await trigger.click();
		expect(
			await screen.findByText(/no families listed for this group/i),
		).toBeInTheDocument();
	});
});

it("renders botanical group with null rotation years as Perennial", () => {
	(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue({
		data: [
			{
				botanical_group_id: 1,
				botanical_group_name: "Group 1",
				rotate_years: null,
				families: [],
			},
		],
		isLoading: false,
		error: null,
		isSuccess: true,
	});
	render(
		<MemoryRouter>
			<BotanicalGroupsPage />
		</MemoryRouter>,
	);
	expect(screen.getByText(/perennial/i)).toBeInTheDocument();
});

it("renders botanical group with multiple families and allows navigation", async () => {
	(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue({
		data: [
			{
				botanical_group_id: 1,
				botanical_group_name: "Group 1",
				rotate_years: 2,
				families: [
					{ family_id: "f1", family_name: "Family One" },
					{ family_id: "f2", family_name: "Family Two" },
				],
			},
		],
		isLoading: false,
		error: null,
		isSuccess: true,
	});
	render(
		<MemoryRouter>
			<BotanicalGroupsPage />
		</MemoryRouter>,
	);
	// Open the accordion to reveal content
	const trigger = screen.getByRole("button", { name: /group 1/i });
	await trigger.click();
	expect(await screen.findByText(/family one/i)).toBeInTheDocument();
	expect(await screen.findByText(/family two/i)).toBeInTheDocument();
});

it("handles group with missing recommended_rotation_years and families fields", async () => {
	(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue({
		data: [{ botanical_group_id: 1, botanical_group_name: "Group 1" }],
		isLoading: false,
		error: null,
		isSuccess: true,
	});
	render(
		<MemoryRouter>
			<BotanicalGroupsPage />
		</MemoryRouter>,
	);
	expect(screen.getByText(/group 1/i)).toBeInTheDocument();
	// Open the accordion to reveal content
	const trigger = screen.getByRole("button", { name: /group 1/i });
	await trigger.click();
	expect(
		await screen.findByText(/no families listed for this group/i),
	).toBeInTheDocument();
});
