import { render, screen, fireEvent } from "@testing-library/react";
import BotanicalGroupsPage from "./BotanicalGroups";
import BotanicalGroupsContainer from "../components/BotanicalGroupsContainer";
import { BotanicalGroupItemContainer } from "../components/BotanicalGroupItemContainer";
import { FamilyInfoPresenter } from "../components/FamilyInfoPresenter";
import FamilyInfoContainer from "../components/FamilyInfoContainer";
import * as BotanicalGroupsHook from "../hooks/useBotanicalGroups";
import * as FamilyInfoHook from "../hooks/useFamilyInfo";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Accordion } from "@/components/ui/Accordion";

// Mock useBotanicalGroups
vi.mock("../hooks/useBotanicalGroups");
vi.mock("../hooks/useFamilyInfo");

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
		fireEvent.click(trigger);
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

describe("BotanicalGroupItemContainer", () => {
	it("renders and passes click to onFamilyClick", async () => {
		const onFamilyClick = vi.fn();
		const group = {
			botanical_group_id: "bg-1",
			botanical_group_name: "Nightshades",
			rotate_years: 3,
			families: [
				{ family_id: "f1", family_name: "Solanaceae" },
				{ family_id: "f2", family_name: "Capsicum" },
			],
		};
		render(
			<Accordion type="single" collapsible>
				<BotanicalGroupItemContainer
					group={group}
					onFamilyClick={onFamilyClick}
				/>
			</Accordion>,
		);
		// Open accordion
		fireEvent.click(screen.getByRole("button", { name: /nightshades/i }));
		// Click a family
		const familyBtn = await screen.findByRole("button", {
			name: /view details for solanaceae/i,
		});
		fireEvent.click(familyBtn);
		expect(onFamilyClick).toHaveBeenCalledWith("f1");
	});

	it("shows perennial for null rotate_years", () => {
		const group = {
			botanical_group_id: "bg-2",
			botanical_group_name: "Herbs",
			rotate_years: null,
			families: [],
		};
		render(
			<Accordion type="single" collapsible>
				<BotanicalGroupItemContainer group={group} onFamilyClick={vi.fn()} />
			</Accordion>,
		);
		expect(screen.getByText(/perennial/i)).toBeInTheDocument();
	});
});

describe("BotanicalGroupsContainer", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders loading state from hook", () => {
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
				<BotanicalGroupsContainer />
			</MemoryRouter>,
		);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("renders error state from hook", () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [],
				isLoading: false,
				error: new Error("Network error"),
				isSuccess: false,
			},
		);
		render(
			<MemoryRouter>
				<BotanicalGroupsContainer />
			</MemoryRouter>,
		);
		expect(screen.getByText(/network error/i)).toBeInTheDocument();
	});

	it("renders empty state when no groups found", () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [],
				isLoading: false,
				error: null,
				isSuccess: true,
			},
		);
		render(
			<MemoryRouter>
				<BotanicalGroupsContainer />
			</MemoryRouter>,
		);
		expect(screen.getByText(/no botanical groups found/i)).toBeInTheDocument();
	});

	it("scrolls to top on mount", () => {
		(BotanicalGroupsHook.useBotanicalGroups as unknown as Mock).mockReturnValue(
			{
				data: [],
				isLoading: false,
				error: null,
				isSuccess: true,
			},
		);
		const scrollToMock = vi.fn();
		Object.defineProperty(window, "scrollTo", {
			value: scrollToMock,
			writable: true,
		});
		render(
			<MemoryRouter>
				<BotanicalGroupsContainer />
			</MemoryRouter>,
		);
		// scrollTo should be called (either main element or window)
		expect(scrollToMock).toHaveBeenCalled();
	});
});

describe("FamilyInfoPresenter", () => {
	it("renders loading state", () => {
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={null}
					isLoading={true}
					error={null}
					isSuccess={false}
				/>
			</MemoryRouter>,
		);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("renders error state", () => {
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={null}
					isLoading={false}
					error={new Error("Failed to load")}
					isSuccess={false}
				/>
			</MemoryRouter>,
		);
		expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
	});

	it("renders not found when success but no data", () => {
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={null}
					isLoading={false}
					error={null}
					isSuccess={true}
				/>
			</MemoryRouter>,
		);
		expect(screen.getByText(/not found/i)).toBeInTheDocument();
	});

	it("returns null when no data and not success", () => {
		const { container } = render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={null}
					isLoading={false}
					error={null}
					isSuccess={false}
				/>
			</MemoryRouter>,
		);
		expect(container.innerHTML).toBe("");
	});

	it("renders family info with diseases and pests", () => {
		const data = {
			family_id: "f1",
			family_name: "Solanaceae",
			botanical_group: {
				botanical_group_id: "bg1",
				botanical_group_name: "Nightshades",
				rotate_years: 3,
			},
			companion_to: [{ family_id: "f2", family_name: "Legumes" }],
			antagonises: [{ family_id: "f3", family_name: "Brassicas" }],
			diseases: [
				{
					disease_id: "d1",
					disease_name: "Blight",
					symptoms: [{ symptom_id: "s1", symptom_name: "Wilting" }],
					treatments: [
						{ intervention_id: "t1", intervention_name: "Fungicide" },
					],
					preventions: [
						{ intervention_id: "p1", intervention_name: "Crop rotation" },
					],
				},
			],
			pests: [
				{
					pest_id: "p1",
					pest_name: "Aphids",
					treatments: [
						{ intervention_id: "t2", intervention_name: "Neem oil" },
					],
					preventions: [
						{ intervention_id: "p2", intervention_name: "Companion planting" },
					],
				},
			],
		};
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={data}
					isLoading={false}
					error={null}
					isSuccess={true}
				/>
			</MemoryRouter>,
		);
		expect(screen.getByText(/solanaceae/i)).toBeInTheDocument();
		expect(screen.getByText(/nightshades/i)).toBeInTheDocument();
		expect(screen.getByText(/3 year\(s\)/i)).toBeInTheDocument();
		expect(screen.getByText(/legumes/i)).toBeInTheDocument();
		expect(screen.getByText(/brassicas/i)).toBeInTheDocument();
		expect(screen.getByText(/blight/i)).toBeInTheDocument();
		expect(screen.getByText(/wilting/i)).toBeInTheDocument();
		expect(screen.getByText(/fungicide/i)).toBeInTheDocument();
		expect(screen.getByText(/crop rotation/i)).toBeInTheDocument();
		expect(screen.getByText(/aphids/i)).toBeInTheDocument();
		expect(screen.getByText(/neem oil/i)).toBeInTheDocument();
	});

	it("renders empty lists text when no diseases/pests/companions/antagonists", () => {
		const data = {
			family_id: "f1",
			family_name: "Empty Family",
			botanical_group: {
				botanical_group_id: "bg1",
				botanical_group_name: "Group A",
				rotate_years: null,
			},
			companion_to: [],
			antagonises: [],
			diseases: [],
			pests: [],
		};
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={data}
					isLoading={false}
					error={null}
					isSuccess={true}
				/>
			</MemoryRouter>,
		);
		expect(
			screen.getByText(/no companion families listed/i),
		).toBeInTheDocument();
		expect(
			screen.getByText(/no antagonist families listed/i),
		).toBeInTheDocument();
		expect(screen.getByText(/no diseases listed/i)).toBeInTheDocument();
		expect(screen.getByText(/no pests listed/i)).toBeInTheDocument();
		expect(screen.getByText(/perennial/i)).toBeInTheDocument();
	});

	it("renders disease with no symptoms/treatments/preventions", () => {
		const data = {
			family_id: "f1",
			family_name: "Test Family",
			botanical_group: {
				botanical_group_id: "bg1",
				botanical_group_name: "Group",
				rotate_years: 2,
			},
			diseases: [
				{
					disease_id: "d1",
					disease_name: "Unknown Disease",
					symptoms: [],
					treatments: [],
					preventions: [],
				},
			],
			pests: [
				{
					pest_id: "p1",
					pest_name: "Unknown Pest",
					treatments: [],
					preventions: [],
				},
			],
		};
		render(
			<MemoryRouter>
				<FamilyInfoPresenter
					data={data}
					isLoading={false}
					error={null}
					isSuccess={true}
				/>
			</MemoryRouter>,
		);
		// Should render "None listed" for empty arrays
		const noneListed = screen.getAllByText(/none listed/i);
		expect(noneListed.length).toBeGreaterThanOrEqual(4);
	});
});

describe("FamilyInfoContainer", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders loading state", () => {
		(FamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: undefined,
			isLoading: true,
			error: null,
			isSuccess: false,
		});
		render(
			<MemoryRouter initialEntries={["/family/f1"]}>
				<Routes>
					<Route path="/family/:familyId" element={<FamilyInfoContainer />} />
				</Routes>
			</MemoryRouter>,
		);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("renders error state", () => {
		(FamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: undefined,
			isLoading: false,
			error: new Error("API error"),
			isSuccess: false,
		});
		render(
			<MemoryRouter initialEntries={["/family/f1"]}>
				<Routes>
					<Route path="/family/:familyId" element={<FamilyInfoContainer />} />
				</Routes>
			</MemoryRouter>,
		);
		expect(screen.getByText(/api error/i)).toBeInTheDocument();
	});

	it("renders family data when loaded", () => {
		(FamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: {
				family_id: "f1",
				family_name: "Solanaceae",
				botanical_group: {
					botanical_group_id: "bg1",
					botanical_group_name: "Nightshades",
					rotate_years: 3,
				},
				companion_to: [],
				antagonises: [],
				diseases: [],
				pests: [],
			},
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		render(
			<MemoryRouter initialEntries={["/family/f1"]}>
				<Routes>
					<Route path="/family/:familyId" element={<FamilyInfoContainer />} />
				</Routes>
			</MemoryRouter>,
		);
		expect(screen.getByText(/solanaceae/i)).toBeInTheDocument();
	});
});
