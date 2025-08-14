import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RegisterForm from "./RegisterForm";
import * as AuthContext from "@/store/auth/AuthContext";
import * as RegistrationService from "../services/RegistrationService";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock useAuth
vi.mock("@/store/auth/AuthContext");
// Mock registerUser
vi.mock("../services/RegistrationService");

// Helper to select the first non-empty country option
async function selectFirstCountry() {
	const countrySelect = screen.queryByLabelText(/country/i);
	if (countrySelect && countrySelect.querySelectorAll("option").length > 1) {
		// Find the first non-empty value option
		const options = Array.from(countrySelect.querySelectorAll("option"));
		const firstValid = options.find((opt) => opt.value && opt.value !== "");
		if (firstValid) {
			await userEvent.selectOptions(countrySelect, firstValid.value);
		}
	}
}

// Custom matcher for split text nodes
async function findTextContentMatch(
	matcher: (text: string) => boolean,
	{ timeout = 1000 }: { timeout?: number } = {},
) {
	const start = Date.now();
	let found = null;
	while (Date.now() - start < timeout) {
		found = Array.from(document.body.querySelectorAll("*")).find(
			(node) => node.textContent && matcher(node.textContent),
		);
		if (found) return found;
		vi.useFakeTimers();
		vi.runAllTimers();
		vi.useRealTimers();
	}
	throw new Error(`Text not found: ${matcher.toString()}`);
}

function renderForm() {
	const queryClient = new QueryClient({
		defaultOptions: {
			queries: {
				retry: false,
			},
			mutations: {
				retry: false,
			},
		},
	});

	return render(
		<QueryClientProvider client={queryClient}>
			<MemoryRouter>
				<RegisterForm />
			</MemoryRouter>
		</QueryClientProvider>,
	);
}

describe("RegisterForm", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		(AuthContext.useAuth as unknown as Mock).mockReturnValue({
			login: vi.fn(),
		});
		Object.defineProperty(window.navigator, "onLine", {
			value: true,
			configurable: true,
		});
	});

	it("renders all fields and submit button", () => {
		renderForm();
		expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
		expect(
			screen.getByLabelText(/^password$/i, { selector: "input" }),
		).toBeInTheDocument();
		expect(
			screen.getByLabelText(/confirm password/i, { selector: "input" }),
		).toBeInTheDocument();
		expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /register/i }),
		).toBeInTheDocument();
	});

	it("shows validation errors for empty fields", async () => {
		renderForm();
		await userEvent.click(screen.getByRole("button", { name: /register/i }));
		expect(await screen.findAllByText(/required/i)).not.toHaveLength(0);
	});

	it("toggles password visibility", async () => {
		renderForm();
		const passwordInput = screen.getByLabelText(/^password$/i, {
			selector: "input",
		});
		const toggleBtns = screen.getAllByRole("button", {
			name: /show password/i,
		});
		expect(passwordInput).toHaveAttribute("type", "password");
		await userEvent.click(toggleBtns[0]);
		expect(passwordInput).toHaveAttribute("type", "text");
		await userEvent.click(toggleBtns[0]);
		expect(passwordInput).toHaveAttribute("type", "password");
	});

	it("toggles confirm password visibility", async () => {
		renderForm();
		const confirmInput = screen.getByLabelText(/confirm password/i, {
			selector: "input",
		});
		const toggleBtns = screen.getAllByRole("button", {
			name: /show password/i,
		});
		expect(confirmInput).toHaveAttribute("type", "password");
		await userEvent.click(toggleBtns[1]);
		expect(confirmInput).toHaveAttribute("type", "text");
		await userEvent.click(toggleBtns[1]);
		expect(confirmInput).toHaveAttribute("type", "password");
	});
});
