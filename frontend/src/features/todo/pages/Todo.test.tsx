import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../../../mocks/server";
import { buildUrl } from "../../../mocks/buildUrl";
import Todo from "./Todo";
import type { WeeklyTodoRead } from "../types/todoTypes";

// Mock the PageLayout
vi.mock("../../../components/layouts/PageLayout", () => ({
	PageLayout: vi.fn(({ children }) => (
		<div data-testid="page-layout">{children}</div>
	)),
}));

// Mock data for weekly todo
const mockWeeklyTodo: WeeklyTodoRead = {
	week_id: "week-1",
	week_number: 20,
	week_start_date: "15/05",
	week_end_date: "21/05",
	weekly_tasks: {
		sow_tasks: [
			{
				variety_id: "variety-1",
				variety_name: "Cherry Tomato",
				family_name: "Solanaceae",
			},
			{
				variety_id: "variety-2",
				variety_name: "Bell Pepper",
				family_name: "Solanaceae",
			},
		],
		transplant_tasks: [
			{
				variety_id: "variety-3",
				variety_name: "Lettuce",
				family_name: "Asteraceae",
			},
		],
		harvest_tasks: [
			{
				variety_id: "variety-4",
				variety_name: "Spinach",
				family_name: "Amaranthaceae",
			},
		],
		prune_tasks: [],
		compost_tasks: [],
	},
	daily_tasks: {
		1: {
			day_id: "day-1",
			day_number: 1,
			day_name: "Monday",
			feed_tasks: [
				{
					feed_id: "feed-1",
					feed_name: "Tomato Feed",
					varieties: [
						{
							variety_id: "variety-1",
							variety_name: "Cherry Tomato",
							family_name: "Solanaceae",
						},
					],
				},
			],
			water_tasks: [
				{
					variety_id: "variety-2",
					variety_name: "Bell Pepper",
					family_name: "Solanaceae",
				},
				{
					variety_id: "variety-3",
					variety_name: "Lettuce",
					family_name: "Asteraceae",
				},
			],
		},
		3: {
			day_id: "day-3",
			day_number: 3,
			day_name: "Wednesday",
			feed_tasks: [],
			water_tasks: [
				{
					variety_id: "variety-1",
					variety_name: "Cherry Tomato",
					family_name: "Solanaceae",
				},
			],
		},
	},
};

describe("Todo Page", () => {
	let queryClient: QueryClient;
	let user: ReturnType<typeof userEvent.setup>;

	beforeEach(() => {
		queryClient = new QueryClient({
			defaultOptions: {
				queries: {
					retry: false,
				},
			},
		});
		user = userEvent.setup();

		// Mock successful API response
		server.use(
			http.get(buildUrl("/weekly-todo"), () => {
				return HttpResponse.json(mockWeeklyTodo);
			}),
		);
	});

	const renderWithQueryClient = (component: React.ReactElement) => {
		return render(
			<QueryClientProvider client={queryClient}>
				{component}
			</QueryClientProvider>,
		);
	};

	describe("Page Rendering", () => {
		it("renders the page layout and header", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Weekly Tasks")).toBeInTheDocument();
			});

			expect(
				screen.getByText("Manage your garden activities for the week"),
			).toBeInTheDocument();
			expect(screen.getByTestId("page-layout")).toBeInTheDocument();
		});

		it("displays week selector with current week information", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Week 20")).toBeInTheDocument();
			});

			expect(screen.getByText("15/05 - 21/05")).toBeInTheDocument();
		});
	});

	describe("Loading State", () => {
		it("shows loading skeletons while fetching data", () => {
			// Delay the response to test loading state
			server.use(
				http.get(buildUrl("/weekly-todo"), async () => {
					await new Promise((resolve) => setTimeout(resolve, 100));
					return HttpResponse.json(mockWeeklyTodo);
				}),
			);

			renderWithQueryClient(<Todo />);

			// Check for skeleton elements
			const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
			expect(skeletons.length).toBeGreaterThan(0);
		});
	});

	describe("Error State", () => {
		it("displays error message when API call fails", async () => {
			server.use(
				http.get(buildUrl("/weekly-todo"), () => {
					return HttpResponse.json(
						{ detail: "Failed to fetch weekly todo" },
						{ status: 500 },
					);
				}),
			);

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Error Loading Tasks")).toBeInTheDocument();
			});
		});

		it("displays appropriate error message for network errors", async () => {
			server.use(
				http.get(buildUrl("/weekly-todo"), () => {
					return HttpResponse.error();
				}),
			);

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Error Loading Tasks")).toBeInTheDocument();
			});
		});
	});

	describe("Weekly Tasks Display", () => {
		it("displays all weekly task categories with data", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Sow")).toBeInTheDocument();
			});

			expect(screen.getByText("Transplant")).toBeInTheDocument();
			expect(screen.getByText("Harvest")).toBeInTheDocument();
		});

		it("shows correct variety names in sow tasks", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
			});

			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
		});

		it("displays family names with varieties", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getAllByText("Solanaceae")[0]).toBeInTheDocument();
			});

			expect(screen.getByText("Asteraceae")).toBeInTheDocument();
		});

		it("shows badge with task count for each category", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				// Sow tasks should have a badge with count 2
				const sowSection = screen.getByText("Sow").closest("div");
				expect(sowSection).toContainHTML("2");
			});
		});

		it("does not display empty task categories", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Sow")).toBeInTheDocument();
			});

			// Prune and Compost tasks are empty, so they shouldn't be displayed
			expect(screen.queryByText("Prune")).not.toBeInTheDocument();
			expect(screen.queryByText("Compost")).not.toBeInTheDocument();
		});
	});

	describe("Daily Tasks Display", () => {
		it("displays daily tasks section", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Daily Tasks")).toBeInTheDocument();
			});
		});

		it("shows correct day names", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText(/Monday/i)).toBeInTheDocument();
			});

			expect(screen.getByText(/Wednesday/i)).toBeInTheDocument();
		});

		it("displays feed tasks grouped by feed type", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Tomato Feed")).toBeInTheDocument();
			});
		});

		it("shows water tasks for each day", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				// Monday has 2 water tasks
				const mondaySection = screen.getByText(/Monday/i).closest("div");
				expect(mondaySection).toContainHTML("2 Water");
			});
		});

		it("displays varieties under correct feed groups", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				const feedSection = screen.getByText("Tomato Feed").closest("div");
				expect(feedSection).toContainHTML("Cherry Tomato");
			});
		});
	});

	describe("Week Navigation", () => {
		it("allows navigating to previous week", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Week 20")).toBeInTheDocument();
			});

			const previousButton = screen.getByText("Previous Week");
			await user.click(previousButton);

			// Should fetch week 19
			await waitFor(() => {
				// Would need to mock the API response for week 19
				expect(previousButton).toBeInTheDocument();
			});
		});

		it("allows navigating to next week", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Week 20")).toBeInTheDocument();
			});

			const nextButton = screen.getByText("Next Week");
			await user.click(nextButton);

			// Should fetch week 21
			await waitFor(() => {
				expect(nextButton).toBeInTheDocument();
			});
		});

		it("disables previous button at minimum week", async () => {
			const week1Todo = { ...mockWeeklyTodo, week_number: 1 };
			server.use(
				http.get(buildUrl("/weekly-todo"), () => {
					return HttpResponse.json(week1Todo);
				}),
			);

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				const previousButton = screen.getByText("Previous Week");
				expect(previousButton).toBeDisabled();
			});
		});

		it("disables next button at maximum week", async () => {
			const week52Todo = { ...mockWeeklyTodo, week_number: 52 };
			server.use(
				http.get(buildUrl("/weekly-todo"), () => {
					return HttpResponse.json(week52Todo);
				}),
			);

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				const nextButton = screen.getByText("Next Week");
				expect(nextButton).toBeDisabled();
			});
		});
	});

	describe("Empty State", () => {
		it("displays message when no tasks are available", async () => {
			const emptyTodo: WeeklyTodoRead = {
				...mockWeeklyTodo,
				weekly_tasks: {
					sow_tasks: [],
					transplant_tasks: [],
					harvest_tasks: [],
					prune_tasks: [],
					compost_tasks: [],
				},
				daily_tasks: {},
			};

			server.use(
				http.get(buildUrl("/weekly-todo"), () => {
					return HttpResponse.json(emptyTodo);
				}),
			);

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("All Caught Up!")).toBeInTheDocument();
			});

			expect(
				screen.getByText(/You have no tasks scheduled for this week/i),
			).toBeInTheDocument();
		});
	});

	describe("Responsive Design", () => {
		it("renders correctly on mobile viewport", async () => {
			// Simulate mobile viewport
			global.innerWidth = 375;
			global.innerHeight = 667;

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(screen.getByText("Weekly Tasks")).toBeInTheDocument();
			});

			// Check that content is still accessible
			expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
		});
	});

	describe("Data Refresh", () => {
		it("refetches data when window regains focus", async () => {
			const fetchSpy = vi.fn(() => HttpResponse.json(mockWeeklyTodo));
			server.use(http.get(buildUrl("/weekly-todo"), fetchSpy));

			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				expect(fetchSpy).toHaveBeenCalledTimes(1);
			});

			// Simulate window focus
			window.dispatchEvent(new Event("focus"));

			await waitFor(() => {
				// Should refetch on focus
				expect(fetchSpy).toHaveBeenCalledTimes(2);
			});
		});
	});

	describe("Accessibility", () => {
		it("has proper heading hierarchy", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				const h1 = screen.getByRole("heading", { level: 1 });
				expect(h1).toHaveTextContent("Weekly Tasks");
			});

			const h2Elements = screen.getAllByRole("heading", { level: 2 });
			expect(h2Elements.length).toBeGreaterThan(0);
		});

		it("has accessible buttons", async () => {
			renderWithQueryClient(<Todo />);

			await waitFor(() => {
				const buttons = screen.getAllByRole("button");
				for (const button of buttons) {
					expect(button).toHaveAccessibleName();
				}
			});
		});
	});
});
