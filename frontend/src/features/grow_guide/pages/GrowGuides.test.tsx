import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import GrowGuides from "./GrowGuides";
import { growGuideService } from "../services/growGuideService";

// Mock the dependencies
vi.mock("../components/GrowGuideListContainer", () => ({
	GrowGuideListContainer: vi.fn(({ onSelect, selectedVarietyId }) => (
		<div data-testid="grow-guide-list-container">
			<button type="button" onClick={() => onSelect("test-variety-id")}>Select Guide</button>
			<div>Selected: {selectedVarietyId || "none"}</div>
		</div>
	)),
}));

vi.mock("../forms/GrowGuideForm", () => ({
	GrowGuideForm: vi.fn(({ isOpen, onClose, varietyId, mode }) => (
		<div data-testid="grow-guide-form">
			{isOpen && (
				<div>
					<div>Form is open</div>
					<div>Mode: {mode}</div>
					<div>Variety ID: {varietyId || "none"}</div>
					<button type="button" onClick={onClose}>Close Form</button>
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
	},
}));

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

		expect(screen.getByTestId("grow-guide-list-container")).toBeInTheDocument();
	});

	it("opens form in create mode when Add New Guide is clicked", () => {
		renderWithQueryClient(<GrowGuides />);

		const addButton = screen.getByText("Add New Guide");
		fireEvent.click(addButton);

		expect(screen.getByText("Form is open")).toBeInTheDocument();
		expect(screen.getByText("Mode: create")).toBeInTheDocument();
		expect(screen.getByText("Variety ID: none")).toBeInTheDocument();
	});

	it("opens form in edit mode when a guide is selected", () => {
		renderWithQueryClient(<GrowGuides />);

		const selectButton = screen.getByText("Select Guide");
		fireEvent.click(selectButton);

		expect(screen.getByText("Form is open")).toBeInTheDocument();
		expect(screen.getByText("Mode: edit")).toBeInTheDocument();
		expect(screen.getByText("Variety ID: test-variety-id")).toBeInTheDocument();
	});

	it("closes the form when close button is clicked", () => {
		renderWithQueryClient(<GrowGuides />);

		// Open the form
		const addButton = screen.getByText("Add New Guide");
		fireEvent.click(addButton);

		expect(screen.getByText("Form is open")).toBeInTheDocument();

		// Close the form
		const closeButton = screen.getByText("Close Form");
		fireEvent.click(closeButton);

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
