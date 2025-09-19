import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, expect, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../../../mocks/server";
import { buildUrl } from "../../../mocks/buildUrl";
import { useUserGrowGuides } from "../hooks/useUserGrowGuides";
import { GrowGuideListContainer } from "./GrowGuideListContainer";
import { GrowGuideListPresenter } from "./GrowGuideListPresenter";
import type { VarietyListRead } from "../types/growGuideTypes";
import {
	growGuideService,
	type VarietyList,
} from "../services/growGuideService";

// Mock the hook
vi.mock("../hooks/useUserGrowGuides");

// Mock data
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
	},
];

describe("GrowGuideListContainer", () => {
	let queryClient: QueryClient;
	let mockOnSelect: ReturnType<typeof vi.fn>;
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
		it("shows loading state while fetching grow guides", async () => {
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

			// Should show loading state initially
			expect(
				document.querySelector('[data-slot="skeleton"]'),
			).toBeInTheDocument();
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
