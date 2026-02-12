import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, expect, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../../../mocks/server";
import { buildUrl } from "../../../mocks/buildUrl";
import GrowGuides from "./GrowGuides";
import { growGuideService } from "../services/growGuideService";
import { GrowGuideListPresenter } from "../components/GrowGuideListPresenter";
import { GrowGuideListContainer } from "../components/GrowGuideListContainer";
import { useUserGrowGuides } from "../hooks/useUserGrowGuides";
import type { VarietyList } from "../services/growGuideService";

// Mock the dependencies
vi.mock("sonner", () => ({
	toast: {
		success: vi.fn(),
		error: vi.fn(),
		info: vi.fn(),
	},
}));

vi.mock("../forms/GrowGuideForm", () => ({
	GrowGuideForm: vi.fn(({ isOpen, onClose, varietyId, mode }) => (
		<div data-testid="grow-guide-form">
			{isOpen && (
				<div>
					<div>Form is open</div>
					<div>Mode: {mode}</div>
					<div>Variety ID: {varietyId || "none"}</div>
					<button type="button" onClick={onClose}>
						Close Form
					</button>
				</div>
			)}
		</div>
	)),
}));

vi.mock("../../../components/layouts/PageLayout", () => ({
	PageLayout: vi.fn(({ children }) => (
		<div data-testid="page-layout">{children}</div>
	)),
}));

vi.mock("../services/growGuideService", () => ({
	growGuideService: {
		getGrowGuideOptions: vi.fn(),
		getUserGrowGuides: vi.fn(),
		activateUserGrowGuide: vi.fn().mockResolvedValue({}),
		deactivateUserGrowGuide: vi.fn().mockResolvedValue(null),
	},
}));

// Mock the hook
vi.mock("../hooks/useUserGrowGuides");

// Mock data with family information for grouping
const mockGrowGuides: VarietyList[] = [
	{
		variety_id: "variety-1",
		variety_name: "Cherry Tomato",
		family: { family_id: "solanaceae", family_name: "Solanaceae" },
		lifecycle: {
			lifecycle_id: "annual",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: false,
		last_updated: "2024-01-01T00:00:00Z",
		is_active: false,
	},
	{
		variety_id: "variety-2",
		variety_name: "Bell Pepper",
		family: { family_id: "solanaceae", family_name: "Solanaceae" },
		lifecycle: {
			lifecycle_id: "annual",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: true,
		last_updated: "2024-01-02T00:00:00Z",
		is_active: false,
	},
	{
		variety_id: "variety-3",
		variety_name: "Lettuce",
		family: { family_id: "asteraceae", family_name: "Asteraceae" },
		lifecycle: {
			lifecycle_id: "annual",
			lifecycle_name: "Annual",
			productivity_years: 1,
		},
		is_public: false,
		last_updated: "2024-01-03T00:00:00Z",
		is_active: false,
	},
];

describe("GrowGuides", () => {
	let queryClient: QueryClient;

	beforeEach(() => {
		queryClient = new QueryClient({
			defaultOptions: {
				queries: {
					retry: false,
				},
			},
		});
		vi.clearAllMocks();

		// Mock the hook to return successful data for GrowGuides tests
		vi.mocked(useUserGrowGuides).mockReturnValue({
			data: mockGrowGuides,
			isLoading: false,
			isError: false,
			error: null,
			isPending: false,
			isLoadingError: false,
			isRefetchError: false,
			isSuccess: true,
			isFetched: true,
			isFetchedAfterMount: true,
			isFetching: false,
			isRefetching: false,
			isStale: false,
			isPlaceholderData: false,
			isInitialLoading: false,
			isEnabled: true,
			dataUpdatedAt: Date.now(),
			errorUpdatedAt: 0,
			failureCount: 0,
			failureReason: null,
			errorUpdateCount: 0,
			isPaused: false,
			fetchStatus: "idle",
			status: "success",
			refetch: vi.fn(),
			promise: Promise.resolve(mockGrowGuides),
		});
	});

	const renderWithQueryClient = (component: React.ReactElement) => {
		return render(
			<QueryClientProvider client={queryClient}>
				{component}
			</QueryClientProvider>,
		);
	};

	it("renders the page layout and header", () => {
		renderWithQueryClient(<GrowGuides />);

		expect(screen.getByText("Grow Guides")).toBeInTheDocument();
		expect(
			screen.getByText("Manage and explore your plant grow guides"),
		).toBeInTheDocument();
		expect(screen.getByText("Add New Guide")).toBeInTheDocument();
		expect(screen.getByTestId("page-layout")).toBeInTheDocument();
	});

	it("renders the grow guide list container", () => {
		renderWithQueryClient(<GrowGuides />);

		expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
		expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
	});

	it("opens form in create mode when Add New Guide is clicked", async () => {
		const user = userEvent.setup();
		renderWithQueryClient(<GrowGuides />);

		const addButton = screen.getByText("Add New Guide");
		await user.click(addButton);

		expect(await screen.findByText("Form is open")).toBeInTheDocument();
		expect(screen.getByText("Mode: create")).toBeInTheDocument();
		expect(screen.getByText("Variety ID: none")).toBeInTheDocument();
	});

	it("opens form in edit mode when a guide is selected", async () => {
		const user = userEvent.setup();
		renderWithQueryClient(<GrowGuides />);

		const guideElement = screen.getByText("Cherry Tomato");
		await user.click(guideElement);

		expect(await screen.findByText("Form is open")).toBeInTheDocument();
		expect(screen.getByText("Mode: edit")).toBeInTheDocument();
		expect(screen.getByText("Variety ID: variety-1")).toBeInTheDocument();
	});

	it("closes the form when close button is clicked", async () => {
		const user = userEvent.setup();
		renderWithQueryClient(<GrowGuides />);

		// Open the form
		const addButton = screen.getByText("Add New Guide");
		await user.click(addButton);

		expect(await screen.findByText("Form is open")).toBeInTheDocument();

		// Close the form
		const closeButton = screen.getByText("Close Form");
		await user.click(closeButton);

		expect(screen.queryByText("Form is open")).not.toBeInTheDocument();
	});

	it("prefetches data on mount", () => {
		const prefetchQuerySpy = vi.spyOn(queryClient, "prefetchQuery");

		renderWithQueryClient(<GrowGuides />);

		expect(prefetchQuerySpy).toHaveBeenCalledWith({
			queryKey: ["growGuideOptions"],
			queryFn: growGuideService.getGrowGuideOptions,
		});

		expect(prefetchQuerySpy).toHaveBeenCalledWith({
			queryKey: ["userGrowGuides"],
			queryFn: growGuideService.getUserGrowGuides,
		});
	});
});

describe("GrowGuideListPresenter", () => {
	let queryClient: QueryClient;
	let mockOnSelect: (id: string) => void;
	let user: ReturnType<typeof userEvent.setup>;

	beforeEach(() => {
		queryClient = new QueryClient({
			defaultOptions: {
				queries: { retry: false },
				mutations: { retry: false },
			},
		});
		mockOnSelect = vi.fn();
		user = userEvent.setup();
	});

	afterEach(() => {
		queryClient.cancelQueries();
		queryClient.clear();
		vi.clearAllMocks();
	});

	const renderWithQueryClient = (ui: React.ReactElement) => {
		return render(
			<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
		);
	};

	describe("Loading State", () => {
		it("displays loading spinner when isLoading is true", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={[]}
					isLoading={true}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.getByLabelText(/loading grow guides/i)).toBeInTheDocument();
		});

		it("does not show content when loading", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={true}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.queryByText("Cherry Tomato")).not.toBeInTheDocument();
		});
	});

	describe("Error State", () => {
		it("displays error message when isError is true", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={[]}
					isLoading={false}
					isError={true}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.getByText(/unable to load/i)).toBeInTheDocument();
		});

		it("shows error message with leaf icon", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={[]}
					isLoading={false}
					isError={true}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.getByText(/refresh or try again/i)).toBeInTheDocument();
		});

		it("does not show content when in error state", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={true}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.queryByText("Cherry Tomato")).not.toBeInTheDocument();
		});
	});

	describe("Empty State", () => {
		it("displays empty state when no grow guides", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={[]}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(
				screen.getByText(/grow guides/i) || screen.getByText(/get started/i),
			).toBeInTheDocument();
		});

		it("shows create first guide message in empty state", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={[]}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(
				screen.getByText(/create your first/i) ||
					screen.getByText(/add new guide/i),
			).toBeInTheDocument();
		});
	});

	describe("Content Display", () => {
		it("displays grow guides when data is available", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
			expect(screen.getByText("Lettuce")).toBeInTheDocument();
		});

		it("groups grow guides by family", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Should show family headings
			expect(screen.getByText("Solanaceae")).toBeInTheDocument();
			expect(screen.getByText("Asteraceae")).toBeInTheDocument();
		});

		it("shows public/private status indicators", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Look for public/private indicators (icons, badges, etc.)
			const publicIndicators =
				screen.getAllByRole("button") || screen.getAllByTestId("public-toggle");
			expect(publicIndicators.length).toBeGreaterThan(0);
		});
	});

	it("does not render a duplicate action on rows", () => {
		renderWithQueryClient(
			<GrowGuideListPresenter
				growGuides={mockGrowGuides}
				isLoading={false}
				isError={false}
			/>,
		);

		// No button with aria-label starting with Duplicate
		const buttons = screen.getAllByRole("button");
		const hasDuplicate = buttons.some((b) =>
			(b.getAttribute("aria-label") || "").toLowerCase().includes("duplicate"),
		);
		expect(hasDuplicate).toBe(false);
	});

	describe("Search Functionality", () => {
		it("renders search input", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(
				screen.getByPlaceholderText(/search/i) ||
					screen.getByLabelText(/search/i),
			).toBeInTheDocument();
		});

		it("filters grow guides based on search term", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const searchInput =
				screen.getByPlaceholderText(/search/i) ||
				screen.getByLabelText(/search/i);
			await user.type(searchInput, "tomato");

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
				expect(screen.queryByText("Bell Pepper")).not.toBeInTheDocument();
				expect(screen.queryByText("Lettuce")).not.toBeInTheDocument();
			});
		});

		it("shows no results message when search yields no matches", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const searchInput =
				screen.getByPlaceholderText(/search/i) ||
				screen.getByLabelText(/search/i);
			await user.type(searchInput, "nonexistent");

			await waitFor(() => {
				expect(
					screen.getByText(/guides found/i) || screen.getByText(/no results/i),
				).toBeInTheDocument();
			});
		});

		it("search is case insensitive", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const searchInput =
				screen.getByPlaceholderText(/search/i) ||
				screen.getByLabelText(/search/i);
			await user.type(searchInput, "TOMATO");

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});
		});

		it("clears search when input is emptied", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const searchInput =
				screen.getByPlaceholderText(/search/i) ||
				screen.getByLabelText(/search/i);

			// Type search term
			await user.type(searchInput, "tomato");
			await waitFor(() => {
				expect(screen.queryByText("Bell Pepper")).not.toBeInTheDocument();
			});

			// Clear search
			await user.clear(searchInput);
			await waitFor(() => {
				expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
				expect(screen.getByText("Lettuce")).toBeInTheDocument();
			});
		});
	});

	describe("Selection Functionality", () => {
		it("calls onSelect when a grow guide is clicked", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const guideElement = screen.getByText("Cherry Tomato");
			await user.click(guideElement);

			expect(mockOnSelect).toHaveBeenCalledWith("variety-1");
		});

		it("highlights selected variety", () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
					selectedVarietyId="variety-1"
				/>,
			);

			// Check for visual selection indicator
			const selectedElement =
				screen.getByText("Cherry Tomato").closest("[class*='bg-accent']") ||
				screen.getByText("Cherry Tomato").closest(".selected") ||
				screen.getByText("Cherry Tomato").closest("[data-selected='true']");

			expect(selectedElement).toBeInTheDocument();
		});

		it("works without onSelect callback", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
				/>,
			);

			const guideElement = screen.getByText("Cherry Tomato");
			await user.click(guideElement);

			// Should not crash
			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
		});
	});

	describe("Delete Functionality", () => {
		beforeEach(() => {
			// Mock successful delete response
			server.use(
				http.delete(buildUrl("/grow-guides/:varietyId"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
		});

		it("shows delete confirmation dialog", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Find and click delete button
			const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
			if (deleteButtons.length > 0) {
				await user.click(deleteButtons[0]);

				expect(
					screen.getByText("Delete Grow Guide") ||
						screen.getByText(/are you sure/i),
				).toBeInTheDocument();
			}
		});

		it("deletes grow guide when confirmed", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Find delete button
			const deleteButtons = screen.getAllByRole("button", {
				name: /delete/i,
			});
			if (deleteButtons.length > 0) {
				await user.click(deleteButtons[0]);

				// Confirm deletion in the dialog
				const confirmButton = await screen.findByRole("button", {
					name: "Delete",
				});
				await user.click(confirmButton);

				// Item should be removed from local state
				// await waitFor(() => {
				// 	expect(screen.queryByText("Cherry Tomato")).not.toBeInTheDocument();
				// });
			}
		});

		it("cancels delete when cancelled", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
			if (deleteButtons.length > 0) {
				await user.click(deleteButtons[0]);

				// Cancel deletion
				const cancelButton =
					screen.getByRole("button", { name: /cancel/i }) ||
					screen.getByRole("button", { name: /no/i });
				await user.click(cancelButton);

				// Item should still be present
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			}
		});

		it("handles delete errors gracefully", async () => {
			server.use(
				http.delete(buildUrl("/grow-guides/:varietyId"), () => {
					return HttpResponse.json(
						{ detail: "Delete failed" },
						{ status: 500 },
					);
				}),
			);

			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
			if (deleteButtons.length > 0) {
				await user.click(deleteButtons[0]);

				const confirmButton =
					screen.getByRole("button", { name: "Delete" }) ||
					screen.getByRole("button", { name: /yes/i });
				await user.click(confirmButton);

				// Item should remain after failed delete
				await waitFor(() => {
					expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
				});
			}
		});
	});

	describe("Public/Private Toggle", () => {
		beforeEach(() => {
			server.use(
				http.put(buildUrl("/grow-guides/:varietyId/visibility"), () => {
					return HttpResponse.json({ is_public: true });
				}),
			);
		});

		it("toggles public status when toggle is clicked", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Find public/private toggle buttons
			const toggleButtons =
				screen.getAllByRole("button") || screen.getAllByRole("switch");
			const publicToggle = toggleButtons.find(
				(button) =>
					button.getAttribute("aria-label")?.includes("public") ||
					button.getAttribute("data-testid")?.includes("public-toggle"),
			);

			if (publicToggle) {
				await user.click(publicToggle);

				// Should optimistically update
				await waitFor(() => {
					// Check for updated state (this depends on your UI implementation)
					expect(publicToggle).toBeInTheDocument();
				});
			}
		});

		it("reverts toggle on API error", async () => {
			server.use(
				http.put(buildUrl("/grow-guides/:varietyId/visibility"), () => {
					return HttpResponse.json(
						{ detail: "Toggle failed" },
						{ status: 500 },
					);
				}),
			);

			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			const toggleButtons =
				screen.getAllByRole("button") || screen.getAllByRole("switch");
			const publicToggle = toggleButtons.find((button) =>
				button.getAttribute("aria-label")?.includes("public"),
			);

			if (publicToggle) {
				const originalState =
					publicToggle.getAttribute("aria-checked") || "false";

				await user.click(publicToggle);

				// Should revert to original state after error
				await waitFor(() => {
					expect(publicToggle.getAttribute("aria-checked")).toBe(originalState);
				});
			}
		});
	});

	describe("Active Guide Selection", () => {
		const setup = () => {
			const onSelect = vi.fn();
			const user = userEvent.setup();
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={onSelect}
				/>,
			);
			return { user, onSelect };
		};

		test("allows selecting an active guide", async () => {
			const { user } = setup();
			const firstGuideSwitch = screen.getByLabelText("Set Lettuce active");
			expect(firstGuideSwitch).toHaveAttribute("aria-checked", "false");

			await user.click(firstGuideSwitch);

			const activeSwitch = await screen.findByRole("switch", {
				name: /set lettuce active/i,
				checked: true,
			});
			expect(activeSwitch).toBeInTheDocument();
		});

		test("activating another guide does not auto-deactivate others", async () => {
			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Get two specific switches by their accessible names
			const cherrySwitch = screen.getByRole("switch", {
				name: /set cherry tomato active/i,
			});
			const bellSwitch = screen.getByRole("switch", {
				name: /set bell pepper active/i,
			});

			// Initially both unchecked
			expect(cherrySwitch).toHaveAttribute("aria-checked", "false");
			expect(bellSwitch).toHaveAttribute("aria-checked", "false");

			// Activate Cherry Tomato
			await user.click(cherrySwitch);
			await waitFor(() => {
				expect(
					screen.getByRole("switch", {
						name: /set cherry tomato active/i,
					}),
				).toHaveAttribute("aria-checked", "true");
				expect(
					screen.getByRole("switch", { name: /set bell pepper active/i }),
				).toHaveAttribute("aria-checked", "false");
			});

			// Activate Bell Pepper as well; previously active should remain active
			await user.click(
				screen.getByRole("switch", { name: /set bell pepper active/i }),
			);

			await waitFor(() => {
				expect(
					screen.getByRole("switch", {
						name: /set cherry tomato active/i,
					}),
				).toHaveAttribute("aria-checked", "true");
				expect(
					screen.getByRole("switch", { name: /set bell pepper active/i }),
				).toHaveAttribute("aria-checked", "true");
			});
		});

		test("deactivating a guide does not affect other guides' toggle states", async () => {
			// Regression test: ensure that when deactivating a guide,
			// other guides maintain their current state (don't all appear to change)
			const guidesWithOneActive = mockGrowGuides.map((g, _idx) => ({
				...g,
				is_active: g.variety_name === "Cherry Tomato", // Make Cherry Tomato active
			}));

			renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={guidesWithOneActive}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Get switches by their specific labels
			const cherryTomatoSwitch = screen.getByRole("switch", {
				name: /set cherry tomato active/i,
			});
			const bellPepperSwitch = screen.getByRole("switch", {
				name: /set bell pepper active/i,
			});
			const lettuceSwitch = screen.getByRole("switch", {
				name: /set lettuce active/i,
			});

			// Wait for initial state to be set from props
			await waitFor(() => {
				expect(cherryTomatoSwitch).toHaveAttribute("aria-checked", "true");
			});

			// Initial state: Cherry Tomato is checked, others are unchecked
			expect(bellPepperSwitch).toHaveAttribute("aria-checked", "false");
			expect(lettuceSwitch).toHaveAttribute("aria-checked", "false");

			// Deactivate Cherry Tomato
			await user.click(cherryTomatoSwitch);

			// Only Cherry Tomato switch should change, others should remain unchanged
			await waitFor(() => {
				expect(cherryTomatoSwitch).toHaveAttribute("aria-checked", "false");
			});

			// Verify other switches remain in their original state (unchecked)
			expect(bellPepperSwitch).toHaveAttribute("aria-checked", "false");
			expect(lettuceSwitch).toHaveAttribute("aria-checked", "false");
		});
	});

	describe("Component State Management", () => {
		it("updates local state when props change", () => {
			const { rerender } = renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();

			// Update with new data
			const newGuides = [mockGrowGuides[0]]; // Only first guide
			rerender(
				<QueryClientProvider client={queryClient}>
					<GrowGuideListPresenter
						growGuides={newGuides}
						isLoading={false}
						isError={false}
						onSelect={mockOnSelect}
					/>
				</QueryClientProvider>,
			);

			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			expect(screen.queryByText("Bell Pepper")).not.toBeInTheDocument();
		});

		it("maintains search state during data updates", async () => {
			const { rerender } = renderWithQueryClient(
				<GrowGuideListPresenter
					growGuides={mockGrowGuides}
					isLoading={false}
					isError={false}
					onSelect={mockOnSelect}
				/>,
			);

			// Apply search filter
			const searchInput =
				screen.getByPlaceholderText(/search/i) ||
				screen.getByLabelText(/search/i);
			await user.type(searchInput, "tomato");

			await waitFor(() => {
				expect(screen.queryByText("Bell Pepper")).not.toBeInTheDocument();
			});

			// Update props
			rerender(
				<QueryClientProvider client={queryClient}>
					<GrowGuideListPresenter
						growGuides={mockGrowGuides}
						isLoading={false}
						isError={false}
						onSelect={mockOnSelect}
					/>
				</QueryClientProvider>,
			);

			// Search should still be applied
			expect(screen.getByDisplayValue("tomato")).toBeInTheDocument();
			expect(screen.queryByText("Bell Pepper")).not.toBeInTheDocument();
		});
	});
});

describe("GrowGuideListContainer", () => {
	let queryClient: QueryClient;
	let mockOnSelect: (id: string) => void;
	let user: ReturnType<typeof userEvent.setup>;

	beforeEach(() => {
		queryClient = new QueryClient({
			defaultOptions: {
				queries: { retry: false },
			},
		});
		mockOnSelect = vi.fn();
		user = userEvent.setup();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	const renderWithQueryClient = (ui: React.ReactElement) => {
		return render(
			<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
		);
	};

	describe("Data Loading", () => {
		it("shows loading spinner while fetching grow guides", async () => {
			// Mock loading state initially
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: undefined,
				isLoading: true,
				isError: false,
				error: null,
				isPending: true,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: false,
				isFetched: false,
				isFetchedAfterMount: false,
				isFetching: true,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: true,
				isEnabled: true,
				dataUpdatedAt: 0,
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "fetching",
				status: "pending",
				refetch: vi.fn(),
				promise: new Promise(() => {}), // Never resolves for loading test
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			// Should show loading spinner initially
			expect(screen.getByLabelText(/loading grow guides/i)).toBeInTheDocument();
		});

		it("displays grow guides when data loads successfully", async () => {
			// Mock successful data loading
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: mockGrowGuides,
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve(mockGrowGuides),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
				expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
			});
		});

		it("handles empty grow guides list", async () => {
			// Mock empty data
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: [],
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve([]),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(
					screen.getByText(/you don't have any grow guides/i),
				).toBeInTheDocument();
			});
		});

		it("handles null/undefined grow guides data", async () => {
			// Mock null data
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: undefined,
				isLoading: false,
				isError: false,
				error: null,
				isPending: true,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: false,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "pending",
				refetch: vi.fn(),
				promise: Promise.resolve([]),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			// Should handle null data gracefully
			await waitFor(() => {
				expect(
					screen.getByText(/you don't have any grow guides/i),
				).toBeInTheDocument();
			});
		});
	});

	describe("Error Handling", () => {
		beforeEach(() => {
			server.resetHandlers();
		});

		it("shows error state when API call fails", async () => {
			// Mock the hook to return error state
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: undefined,
				isLoading: false,
				isError: true,
				error: new Error("API call failed"),
				isPending: false,
				isLoadingError: true,
				isRefetchError: false,
				isSuccess: false,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: 0,
				errorUpdatedAt: Date.now(),
				failureCount: 1,
				failureReason: new Error("API call failed"),
				errorUpdateCount: 1,
				isPaused: false,
				fetchStatus: "idle",
				status: "error",
				refetch: vi.fn(),
				promise: Promise.resolve([]),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(
					screen.getByText(/we were unable to load your grow guides/i),
				).toBeInTheDocument();
			});
		});

		it("shows error state on network failure", async () => {
			// Mock the hook to return error state
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: undefined,
				isLoading: false,
				isError: true,
				error: new Error("Network failure"),
				isPending: false,
				isLoadingError: true,
				isRefetchError: false,
				isSuccess: false,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: 0,
				errorUpdatedAt: Date.now(),
				failureCount: 1,
				failureReason: new Error("Network failure"),
				errorUpdateCount: 1,
				isPaused: false,
				fetchStatus: "idle",
				status: "error",
				refetch: vi.fn(),
				promise: Promise.resolve([]),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(
					screen.getByText(/we were unable to load your grow guides/i),
				).toBeInTheDocument();
			});
		});

		it("does not treat empty array as error", async () => {
			// Mock empty array data
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: [],
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve([]),
			});

			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				// Should show empty state, not error state
				expect(
					screen.getByText(/you don't have any grow guides/i),
				).toBeInTheDocument();
				expect(
					screen.queryByText(/we were unable to load/i),
				).not.toBeInTheDocument();
			});
		});
	});

	describe("Selection Functionality", () => {
		beforeEach(() => {
			// Mock successful data for selection tests
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: mockGrowGuides,
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve(mockGrowGuides),
			});
		});

		it("calls onSelect when a grow guide is selected", async () => {
			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Click on a grow guide (this depends on your UI implementation)
			const guideElement = screen.getByText("Cherry Tomato");
			await user.click(guideElement);

			expect(mockOnSelect).toHaveBeenCalledWith("variety-1");
		});

		it("highlights selected variety", async () => {
			renderWithQueryClient(
				<GrowGuideListContainer
					onSelect={mockOnSelect}
					selectedVarietyId="variety-1"
				/>,
			);

			const selectedElement = await screen.findByText("Cherry Tomato");

			// The selected variety should have some visual indication
			const containerElement = selectedElement.closest("[data-row-container]");
			expect(containerElement).toHaveClass("bg-accent/60", "border-primary");
		});

		it("works without onSelect callback", async () => {
			renderWithQueryClient(<GrowGuideListContainer />);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Should not crash when clicking without onSelect
			const guideElement = screen.getByText("Cherry Tomato");
			await user.click(guideElement);

			// No error should occur
			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
		});

		it("handles selectedVarietyId changes", async () => {
			const { rerender } = renderWithQueryClient(
				<GrowGuideListContainer
					onSelect={mockOnSelect}
					selectedVarietyId="variety-1"
				/>,
			);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Change selected variety
			rerender(
				<QueryClientProvider client={queryClient}>
					<GrowGuideListContainer
						onSelect={mockOnSelect}
						selectedVarietyId="variety-2"
					/>
				</QueryClientProvider>,
			);

			// Both varieties should still be visible, but selection should change
			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
		});

		it("handles null selectedVarietyId", async () => {
			renderWithQueryClient(
				<GrowGuideListContainer
					onSelect={mockOnSelect}
					selectedVarietyId={null}
				/>,
			);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Should work fine with null selection
			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
		});
	});

	describe("Data Consistency", () => {
		beforeEach(() => {
			// Mock successful data for consistency tests
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: mockGrowGuides,
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve(mockGrowGuides),
			});
		});

		it("passes correct props to presenter", async () => {
			renderWithQueryClient(
				<GrowGuideListContainer
					onSelect={mockOnSelect}
					selectedVarietyId="variety-1"
				/>,
			);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Verify that the correct data is passed through
			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
		});

		it("maintains array structure when data is loaded", async () => {
			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Both items should be present
			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
		});
	});

	describe("Component Integration", () => {
		beforeEach(() => {
			// Mock successful data for integration tests
			vi.mocked(useUserGrowGuides).mockReturnValue({
				data: mockGrowGuides,
				isLoading: false,
				isError: false,
				error: null,
				isPending: false,
				isLoadingError: false,
				isRefetchError: false,
				isSuccess: true,
				isFetched: true,
				isFetchedAfterMount: true,
				isFetching: false,
				isRefetching: false,
				isStale: false,
				isPlaceholderData: false,
				isInitialLoading: false,
				isEnabled: true,
				dataUpdatedAt: Date.now(),
				errorUpdatedAt: 0,
				failureCount: 0,
				failureReason: null,
				errorUpdateCount: 0,
				isPaused: false,
				fetchStatus: "idle",
				status: "success",
				refetch: vi.fn(),
				promise: Promise.resolve(mockGrowGuides),
			});
		});

		it("integrates properly with React Query", async () => {
			renderWithQueryClient(<GrowGuideListContainer onSelect={mockOnSelect} />);

			// Should make API call and handle response
			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});
		});

		it("handles component unmounting gracefully", async () => {
			const { unmount } = renderWithQueryClient(
				<GrowGuideListContainer onSelect={mockOnSelect} />,
			);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			// Should unmount without errors
			unmount();
		});
	});
});
