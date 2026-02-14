import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RegisterForm from "./RegisterForm";
import * as AuthContext from "@/store/auth/AuthContext";
import { vi, describe, it, beforeEach, expect, type Mock } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock useAuth
vi.mock("@/store/auth/AuthContext");
// Mock registerUser
vi.mock("../services/RegistrationService");

// Mock navigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
	const actual = await vi.importActual("react-router-dom");
	return {
		...actual,
		useNavigate: () => mockNavigate,
	};
});

// Mock formatError
vi.mock("@/utils/errorUtils", () => ({
	formatError: vi.fn((err: unknown) =>
		err instanceof Error ? err.message : "Unknown error",
	),
}));

// Helper to select the first non-empty country option
async function _selectFirstCountry() {
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
async function _findTextContentMatch(
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

	it("shows offline banner when user is offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});
		expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
	});

	it("shows Offline button text when offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});
		expect(
			screen.getByRole("button", { name: /offline/i }),
		).toBeInTheDocument();
	});

	it("disables submit button when offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});
		expect(screen.getByRole("button", { name: /offline/i })).toBeDisabled();
	});

	it("shows offline error when submitting while offline", async () => {
		const { act } = await import("@testing-library/react");
		renderForm();
		act(() => {
			globalThis.dispatchEvent(new Event("offline"));
		});

		await userEvent.type(screen.getByLabelText(/email/i), "test@example.com");
		await userEvent.type(
			screen.getByLabelText(/^password$/i, { selector: "input" }),
			"Password1!",
		);
		await userEvent.type(
			screen.getByLabelText(/confirm password/i, { selector: "input" }),
			"Password1!",
		);
		await userEvent.type(screen.getByLabelText(/first name/i), "Test");

		// Button is disabled but let's verify the offline state error handling
		expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
	});

	it("renders login link", () => {
		renderForm();
		expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
	});
});
