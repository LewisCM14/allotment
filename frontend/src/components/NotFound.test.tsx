import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NotFound from "./NotFound";
import { MemoryRouter } from "react-router-dom";

import { describe, expect, it, vi, beforeEach } from "vitest";

// Create a shared mock for navigate
const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
	const actual = await vi.importActual("react-router-dom");
	return {
		...actual,
		useNavigate: () => navigateMock,
	};
});

beforeEach(() => {
	navigateMock.mockClear();
});

describe("NotFound", () => {
	it("renders 404 and message", () => {
		render(
			<MemoryRouter>
				<NotFound />
			</MemoryRouter>,
		);
		expect(screen.getByText("404")).toBeInTheDocument();
		expect(screen.getByText("Page Not Found")).toBeInTheDocument();
		expect(
			screen.getByText(
				/the page you are looking for doesn't exist or has been moved/i,
			),
		).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /go back/i }),
		).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /go home/i }),
		).toBeInTheDocument();
	});

	it("calls navigate(-1) when Go Back is clicked", async () => {
		render(
			<MemoryRouter>
				<NotFound />
			</MemoryRouter>,
		);
		await userEvent.click(screen.getByRole("button", { name: /go back/i }));
		expect(navigateMock).toHaveBeenCalledWith(-1);
	});

	it("calls navigate('/') when Go Home is clicked", async () => {
		render(
			<MemoryRouter>
				<NotFound />
			</MemoryRouter>,
		);
		await userEvent.click(screen.getByRole("button", { name: /go home/i }));
		expect(navigateMock).toHaveBeenCalledWith("/");
	});
});
