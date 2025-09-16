import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../../../mocks/server";
import { buildUrl } from "../../../mocks/buildUrl";
import { GrowGuideForm } from "./GrowGuideForm";

describe("GrowGuideForm", () => {
	let queryClient: QueryClient;
	let mockOnClose: ReturnType<typeof vi.fn>;
	let mockOnSuccess: ReturnType<typeof vi.fn>;

	beforeEach(() => {
		queryClient = new QueryClient({
			defaultOptions: {
				queries: { retry: false },
			},
		});
		mockOnClose = vi.fn();
		mockOnSuccess = vi.fn();
	});

	const renderWithQueryClient = (ui: React.ReactElement) => {
		return render(
			<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
		);
	};

	describe("Create Mode", () => {
		it("renders form in create mode", async () => {
			renderWithQueryClient(
				<GrowGuideForm
					mode="create"
					isOpen={true}
					onClose={mockOnClose}
					onSuccess={mockOnSuccess}
				/>,
			);

			// Wait for form fields to load (not just title)
			await waitFor(
				() => {
					expect(screen.getByLabelText(/variety name/i)).toBeInTheDocument();
				},
				{ timeout: 5000 },
			);

			expect(screen.getByText("Add New Grow Guide")).toBeInTheDocument();
			expect(
				screen.getByRole("button", { name: /create guide/i }),
			).toBeInTheDocument();
		});
	});

	describe("Edit Mode", () => {
		beforeEach(() => {
			server.use(
				http.get(buildUrl("/grow-guides/variety-123"), () => {
					return HttpResponse.json({
						id: "variety-123",
						variety_name: "Existing Tomato",
						family_id: "1",
						soil_ph: 6.5,
					});
				}),
			);
		});
	});
});
