import { render, type RenderOptions } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import type React from "react";

// Custom render that includes router context
export function renderWithRouter(
	ui: React.ReactElement,
	options?: Omit<RenderOptions, "queries">,
) {
	return render(<BrowserRouter>{ui}</BrowserRouter>, options);
}
