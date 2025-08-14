import { render, type RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import type React from "react";

// Create a test query client
function createTestQueryClient() {
	return new QueryClient({
		defaultOptions: {
			queries: {
				retry: false, // Disable retries in tests
				gcTime: 0, // Disable cache time in tests
			},
			mutations: {
				retry: false, // Disable retries in tests
			},
		},
	});
}

// Custom render that includes router and React Query context
export function renderWithRouter(
	ui: React.ReactElement,
	options?: Omit<RenderOptions, "queries">,
) {
	const testQueryClient = createTestQueryClient();

	return render(
		<QueryClientProvider client={testQueryClient}>
			<BrowserRouter>{ui}</BrowserRouter>
		</QueryClientProvider>,
		options,
	);
}

// Helper to create a wrapper with React Query for components that don't need router
export function renderWithReactQuery(
	ui: React.ReactElement,
	options?: Omit<RenderOptions, "queries">,
) {
	const testQueryClient = createTestQueryClient();

	return render(
		<QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>,
		options,
	);
}
