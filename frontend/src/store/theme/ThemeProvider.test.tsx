/// <reference types="vitest/globals" />
import { useContext } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "./ThemeProvider";
import { ThemeContext } from "./ThemeContext";
import { vi } from "vitest";

// Helper to consume the context
function ThemeConsumer() {
	const context = useContext(ThemeContext);
	if (!context) return null;
	const { theme, toggleTheme } = context;
	return (
		<>
			<span data-testid="theme">{theme}</span>
			<button type="button" onClick={toggleTheme}>
				Toggle
			</button>
		</>
	);
}

import type { MockInstance } from "vitest";

describe("ThemeProvider", () => {
	let matchMediaMock: MockInstance;
	let getItemMock: MockInstance;
	let setItemMock: MockInstance;

	beforeEach(() => {
		// Mock localStorage (match other test files)
		getItemMock = vi.spyOn(window.localStorage, "getItem");
		setItemMock = vi.spyOn(window.localStorage, "setItem");
		getItemMock.mockImplementation(() => null);
		setItemMock.mockImplementation(() => {});

		// Mock matchMedia – jsdom exposes it on `window` but not on `globalThis`,
		// so we assign a base implementation first, then spy on it.
		globalThis.matchMedia =
			globalThis.matchMedia ??
			((() => ({})) as unknown as typeof globalThis.matchMedia);
		matchMediaMock = vi.spyOn(globalThis, "matchMedia");
		matchMediaMock.mockImplementation(
			(query: string) =>
				({
					matches: query.includes("dark"),
					media: query,
					onchange: null,
					addListener: vi.fn(),
					removeListener: vi.fn(),
					addEventListener: vi.fn(),
					removeEventListener: vi.fn(),
					dispatchEvent: vi.fn(),
				}) as unknown as MediaQueryList,
		);

		// Reset document class
		document.documentElement.className = "";
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("sets initial theme from system preference", () => {
		render(
			<ThemeProvider>
				<ThemeConsumer />
			</ThemeProvider>,
		);
		expect(screen.getByTestId("theme").textContent).toBe("dark");
		expect(document.documentElement.classList.contains("dark")).toBe(true);
		expect(window.localStorage.setItem).toHaveBeenCalledWith("theme", "dark");
	});

	it("toggles theme when toggleTheme is called", () => {
		render(
			<ThemeProvider>
				<ThemeConsumer />
			</ThemeProvider>,
		);
		fireEvent.click(screen.getByText("Toggle"));
		expect(screen.getByTestId("theme").textContent).toBe("light");
		expect(document.documentElement.classList.contains("light")).toBe(true);
		expect(window.localStorage.setItem).toHaveBeenCalledWith("theme", "light");
	});

	it("uses theme from localStorage if available", () => {
		getItemMock.mockReturnValueOnce("light");
		render(
			<ThemeProvider>
				<ThemeConsumer />
			</ThemeProvider>,
		);
		expect(screen.getByTestId("theme").textContent).toBe("light");
		expect(document.documentElement.classList.contains("light")).toBe(true);
	});
});
