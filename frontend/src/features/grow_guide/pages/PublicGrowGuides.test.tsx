import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import React from "react";
import PublicGrowGuides from "./PublicGrowGuides";
import * as AuthContext from "@/store/auth/AuthContext";
import { vi, type Mock } from "vitest";

vi.mock("sonner", () => ({
	toast: {
		success: vi.fn(),
		error: vi.fn(),
		info: vi.fn(),
	},
}));

vi.mock("@/store/auth/AuthContext");

const mockUseAuth = AuthContext.useAuth as unknown as Mock;

function renderPage(isAuthenticated = false) {
	mockUseAuth.mockReturnValue({
		isAuthenticated,
	});
	const queryClient = new QueryClient();
	return render(
		<QueryClientProvider client={queryClient}>
			<MemoryRouter initialEntries={["/public/grow-guides"]}>
				<PublicGrowGuides />
			</MemoryRouter>
		</QueryClientProvider>,
	);
}

describe("PublicGrowGuides Page", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("groups guides by family and sorts alphabetically", async () => {
		renderPage(false);

		await waitFor(() => {
			// Expect the two families from mockPublicGrowGuides: Allium then Cucurbitaceae
			const headings = screen.getAllByRole("heading", { level: 2 });
			expect(headings.length).toBeGreaterThanOrEqual(2);
			expect(headings[0]).toHaveTextContent("Allium");
			expect(headings[1]).toHaveTextContent("Cucurbitaceae");
		});
	});

	it("asks user to log in when copying while unauthenticated", async () => {
		const { container } = renderPage(false);
		const user = userEvent.setup();

		// Expand all families
		const maybeButtons = await screen.findAllByRole("button");
		const triggers = maybeButtons.filter((b) =>
			b.getAttribute("aria-controls"),
		);
		for (const t of triggers) {
			await user.click(t);
		}

		// Click the first "Use this guide" button
		const buttons = await screen.findAllByRole("button", {
			name: /Use this guide/i,
		});
		await user.click(buttons[0]);

		const sonner = await import("sonner");
		expect(sonner.toast.info).toHaveBeenCalled();
	});

	it("copies guide for authenticated user and shows success toast", async () => {
		const { container } = renderPage(true);
		const user = userEvent.setup();

		// Expand all families then click a "Use this guide" button to trigger copy
		const maybeButtons = await screen.findAllByRole("button");
		const triggers = maybeButtons.filter((b) =>
			b.getAttribute("aria-controls"),
		);
		for (const t of triggers) {
			await user.click(t);
		}
		const buttons = await screen.findAllByRole("button", {
			name: /Use this guide/i,
		});
		await user.click(buttons[0]);

		const sonner = await import("sonner");
		await waitFor(() => {
			expect(sonner.toast.success).toHaveBeenCalled();
		});
	});

	it("filters guides by search term", async () => {
		renderPage(false);
		const user = userEvent.setup();
		// Wait for list to load
		await screen.findByRole("textbox", { name: /search public grow guides/i });
		// Expand Allium so items within become visible
		const maybeButtons = await screen.findAllByRole("button");
		const triggers = maybeButtons.filter((b) =>
			b.getAttribute("aria-controls"),
		);
		for (const t of triggers) {
			await user.click(t);
		}
		// Type a search that matches only Spring Onions
		await user.type(
			screen.getByRole("textbox", { name: /search public grow guides/i }),
			"Spring",
		);

		// Expect to see Spring Onions and not Heirloom Carrots
		expect(await screen.findByText(/Spring Onions/i)).toBeInTheDocument();
		expect(screen.queryByText(/Heirloom Carrots/i)).not.toBeInTheDocument();

		// Clear search, both should be visible again
		await user.clear(
			screen.getByRole("textbox", { name: /search public grow guides/i }),
		);
		expect(await screen.findByText(/Heirloom Carrots/i)).toBeInTheDocument();
	});
});
