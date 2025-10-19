// import { render, screen, waitFor } from "@testing-library/react";
// import userEvent from "@testing-library/user-event";
// import { vi, describe, it, beforeEach, expect } from "vitest";
// import { act } from "@testing-library/react";
// import {
// 	QueryClient,
// 	QueryClientProvider,
// 	focusManager,
// } from "@tanstack/react-query";
// import { http, HttpResponse } from "msw";
// import { server } from "../../../mocks/server";
// import { buildUrl } from "../../../mocks/buildUrl";
// import Todo from "./Todo";
// import type { WeeklyTodoRead } from "../types/todoTypes";

// // Mock the PageLayout
// vi.mock("../../../components/layouts/PageLayout", () => ({
// 	PageLayout: vi.fn(({ children }) => (
// 		<div data-testid="page-layout">{children}</div>
// 	)),
// }));

// // Mock data for weekly todo
// const mockWeeklyTodo: WeeklyTodoRead = {
// 	week_id: "week-1",
// 	week_number: 20,
// 	week_start_date: "15/05",
// 	week_end_date: "21/05",
// 	weekly_tasks: {
// 		sow_tasks: [
// 			{
// 				variety_id: "variety-1",
// 				variety_name: "Cherry Tomato",
// 				family_name: "Solanaceae",
// 			},
// 			{
// 				variety_id: "variety-2",
// 				variety_name: "Bell Pepper",
// 				family_name: "Solanaceae",
// 			},
// 		],
// 		transplant_tasks: [
// 			{
// 				variety_id: "variety-3",
// 				variety_name: "Lettuce",
// 				family_name: "Asteraceae",
// 			},
// 		],
// 		harvest_tasks: [
// 			{
// 				variety_id: "variety-4",
// 				variety_name: "Spinach",
// 				family_name: "Amaranthaceae",
// 			},
// 		],
// 		prune_tasks: [],
// 		compost_tasks: [],
// 	},
// 	daily_tasks: {
// 		1: {
// 			day_id: "day-1",
// 			day_number: 1,
// 			day_name: "Monday",
// 			feed_tasks: [
// 				{
// 					feed_id: "feed-1",
// 					feed_name: "Tomato Feed",
// 					varieties: [
// 						{
// 							variety_id: "variety-1",
// 							variety_name: "Cherry Tomato",
// 							family_name: "Solanaceae",
// 						},
// 					],
// 				},
// 			],
// 			water_tasks: [
// 				{
// 					variety_id: "variety-2",
// 					variety_name: "Bell Pepper",
// 					family_name: "Solanaceae",
// 				},
// 				{
// 					variety_id: "variety-3",
// 					variety_name: "Lettuce",
// 					family_name: "Asteraceae",
// 				},
// 			],
// 		},
// 		3: {
// 			day_id: "day-3",
// 			day_number: 3,
// 			day_name: "Wednesday",
// 			feed_tasks: [],
// 			water_tasks: [
// 				{
// 					variety_id: "variety-1",
// 					variety_name: "Cherry Tomato",
// 					family_name: "Solanaceae",
// 				},
// 			],
// 		},
// 	},
// };

// describe("Todo Page", () => {
// 	let queryClient: QueryClient;
// 	let user: ReturnType<typeof userEvent.setup>;

// 	beforeEach(() => {
// 		queryClient = new QueryClient({
// 			defaultOptions: {
// 				queries: {
// 					retry: false,
// 				},
// 			},
// 		});
// 		user = userEvent.setup();

// 		// Mock successful API response
// 		server.use(
// 			http.get(buildUrl("/todos/weekly"), () => {
// 				return HttpResponse.json(mockWeeklyTodo);
// 			}),
// 		);
// 	});

// 	const renderWithQueryClient = (component: React.ReactElement) => {
// 		return render(
// 			<QueryClientProvider client={queryClient}>
// 				{component}
// 			</QueryClientProvider>,
// 		);
// 	};

// 	describe("Page Rendering", () => {
// 		it("renders the page layout and header", async () => {
// 			renderWithQueryClient(<Todo />);

// 			// Ensure the main page header (h1) is present
// 			const h1 = await screen.findByRole("heading", {
// 				level: 1,
// 				name: /Weekly Tasks/i,
// 			});
// 			expect(h1).toBeInTheDocument();

// 			expect(
// 				screen.getByText("Manage your garden activities for the week"),
// 			).toBeInTheDocument();
// 			expect(screen.getByTestId("page-layout")).toBeInTheDocument();
// 		});

// 		it("displays week selector with current week information", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Week 20")).toBeInTheDocument();
// 			});

// 			expect(screen.getByText("15/05 - 21/05")).toBeInTheDocument();
// 		});
// 	});

// 	describe("Loading State", () => {
// 		it("shows loading skeletons while fetching data", () => {
// 			// Delay the response to test loading state
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), async () => {
// 					await new Promise((resolve) => setTimeout(resolve, 100));
// 					return HttpResponse.json(mockWeeklyTodo);
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			// Check for skeleton elements
// 			const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
// 			expect(skeletons.length).toBeGreaterThan(0);
// 		});
// 	});

// 	describe("Error State", () => {
// 		it("displays error message when API call fails", async () => {
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), () => {
// 					return HttpResponse.json(
// 						{ detail: "Failed to fetch weekly todo" },
// 						{ status: 500 },
// 					);
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			// Wait for error alert to render
// 			const errorTitle = await screen.findByText("Error Loading Tasks");
// 			expect(errorTitle).toBeInTheDocument();
// 		});

// 		it("displays appropriate error message for network errors", async () => {
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), () => {
// 					return HttpResponse.error();
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			// Wait for error alert to render
// 			const errorTitle = await screen.findByText("Error Loading Tasks");
// 			expect(errorTitle).toBeInTheDocument();
// 		});
// 	});

// 	describe("Weekly Tasks Display", () => {
// 		it("displays all weekly task categories with data", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Sow")).toBeInTheDocument();
// 			});

// 			expect(screen.getByText("Transplant")).toBeInTheDocument();
// 			expect(screen.getByText("Harvest")).toBeInTheDocument();
// 		});

// 		it("shows correct variety names in sow tasks", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Cherry Tomato")).toBeInTheDocument();
// 			});

// 			expect(screen.getByText("Bell Pepper")).toBeInTheDocument();
// 		});

// 		it("displays family names with varieties", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getAllByText("Solanaceae")[0]).toBeInTheDocument();
// 			});

// 			expect(screen.getByText("Asteraceae")).toBeInTheDocument();
// 		});

// 		it("shows badge with task count for each category", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				// Sow tasks should have a badge with count 2
// 				const sowSection = screen.getByText("Sow").closest("div");
// 				expect(sowSection).toContainHTML("2");
// 			});
// 		});

// 		it("does not display empty task categories", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Sow")).toBeInTheDocument();
// 			});

// 			// Prune and Compost tasks are empty, so they shouldn't be displayed
// 			expect(screen.queryByText("Prune")).not.toBeInTheDocument();
// 			expect(screen.queryByText("Compost")).not.toBeInTheDocument();
// 		});
// 	});

// 	describe("Daily Tasks Display", () => {
// 		it("displays daily tasks section", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Daily Tasks")).toBeInTheDocument();
// 			});
// 		});

// 		it("shows correct day names", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText(/Monday/i)).toBeInTheDocument();
// 			});

// 			expect(screen.getByText(/Wednesday/i)).toBeInTheDocument();
// 		});

// 		it("displays feed tasks grouped by feed type", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Tomato Feed")).toBeInTheDocument();
// 			});
// 		});

// 		it("shows water tasks for each day", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				// Badge shows water task count
// 				expect(screen.getByText(/2\s+Water/i)).toBeInTheDocument();
// 			});
// 		});

// 		it("displays varieties under correct feed groups", async () => {
// 			renderWithQueryClient(<Todo />);

// 			// Ensure feed group label and variety are rendered (allowing duplicates across sections)
// 			const feedLabel = await screen.findByText("Tomato Feed");
// 			expect(feedLabel).toBeInTheDocument();
// 			const varieties = await screen.findAllByText("Cherry Tomato");
// 			expect(varieties.length).toBeGreaterThan(0);
// 		});
// 	});

// 	describe("Week Navigation", () => {
// 		it("allows navigating to previous week", async () => {
// 			// Override handler to assert correct query param and return week 19
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), ({ request }) => {
// 					const url = new URL(request.url);
// 					const wn = url.searchParams.get("week_number");
// 					if (wn) {
// 						// When navigating back, we expect week 19
// 						expect(wn).toBe("19");
// 						return HttpResponse.json({ ...mockWeeklyTodo, week_number: 19 });
// 					}
// 					return HttpResponse.json(mockWeeklyTodo);
// 				}),
// 			);
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Week 20")).toBeInTheDocument();
// 			});

// 			const previousButton = screen.getByText("Previous Week");
// 			await user.click(previousButton);

// 			// Should update to week 19
// 			await screen.findByText("Week 19");
// 		});

// 		it("allows navigating to next week", async () => {
// 			// Override handler to assert correct query param and return week 21
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), ({ request }) => {
// 					const url = new URL(request.url);
// 					const wn = url.searchParams.get("week_number");
// 					if (wn) {
// 						expect(wn).toBe("21");
// 						return HttpResponse.json({ ...mockWeeklyTodo, week_number: 21 });
// 					}
// 					return HttpResponse.json(mockWeeklyTodo);
// 				}),
// 			);
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("Week 20")).toBeInTheDocument();
// 			});

// 			const nextButton = screen.getByText("Next Week");
// 			await user.click(nextButton);

// 			// Should update to week 21
// 			await screen.findByText("Week 21");
// 		});

// 		it("disables previous button at minimum week", async () => {
// 			const week1Todo = { ...mockWeeklyTodo, week_number: 1 };
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), () => {
// 					return HttpResponse.json(week1Todo);
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				const previousButton = screen.getByText("Previous Week");
// 				expect(previousButton).toBeDisabled();
// 			});
// 		});

// 		it("disables next button at maximum week", async () => {
// 			const week52Todo = { ...mockWeeklyTodo, week_number: 52 };
// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), () => {
// 					return HttpResponse.json(week52Todo);
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				const nextButton = screen.getByText("Next Week");
// 				expect(nextButton).toBeDisabled();
// 			});
// 		});
// 	});

// 	describe("Empty State", () => {
// 		it("displays message when no tasks are available", async () => {
// 			const emptyTodo: WeeklyTodoRead = {
// 				...mockWeeklyTodo,
// 				weekly_tasks: {
// 					sow_tasks: [],
// 					transplant_tasks: [],
// 					harvest_tasks: [],
// 					prune_tasks: [],
// 					compost_tasks: [],
// 				},
// 				daily_tasks: {},
// 			};

// 			server.use(
// 				http.get(buildUrl("/todos/weekly"), () => {
// 					return HttpResponse.json(emptyTodo);
// 				}),
// 			);

// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				expect(screen.getByText("All Caught Up!")).toBeInTheDocument();
// 			});

// 			expect(
// 				screen.getByText(/You have no tasks scheduled for this week/i),
// 			).toBeInTheDocument();
// 		});
// 	});

// 	describe("Responsive Design", () => {
// 		it("renders correctly on mobile viewport", async () => {
// 			// Simulate mobile viewport
// 			global.innerWidth = 375;
// 			global.innerHeight = 667;

// 			renderWithQueryClient(<Todo />);

// 			// Check the main header specifically to avoid duplicate text
// 			const h1 = await screen.findByRole("heading", {
// 				level: 1,
// 				name: /Weekly Tasks/i,
// 			});
// 			expect(h1).toBeInTheDocument();

// 			// Check that content is still accessible (allowing multiple occurrences)
// 			const varieties = screen.getAllByText("Cherry Tomato");
// 			expect(varieties.length).toBeGreaterThan(0);
// 		});
// 	});

// 	describe("Data Refresh", () => {
// 		it("refetches data when window regains focus", async () => {
// 			const fetchSpy = vi.fn(() => HttpResponse.json(mockWeeklyTodo));
// 			server.use(http.get(buildUrl("/todos/weekly"), fetchSpy));

// 			// Use a QueryClient with staleTime=0 so focus always refetches
// 			const localClient = new QueryClient({
// 				defaultOptions: {
// 					queries: {
// 						retry: false,
// 						staleTime: 0,
// 						refetchOnWindowFocus: true,
// 					},
// 				},
// 			});

// 			render(
// 				<QueryClientProvider client={localClient}>
// 					<Todo />
// 				</QueryClientProvider>,
// 			);

// 			await waitFor(() => {
// 				expect(fetchSpy).toHaveBeenCalledTimes(1);
// 			});

// 			await act(async () => {
// 				focusManager.setFocused(true);
// 			});

// 			await waitFor(() => {
// 				expect(fetchSpy).toHaveBeenCalledTimes(2);
// 			});
// 		});
// 	});

// 	describe("Accessibility", () => {
// 		it("has proper heading hierarchy", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				const h1 = screen.getByRole("heading", { level: 1 });
// 				expect(h1).toHaveTextContent("Weekly Tasks");
// 			});

// 			const h2Elements = screen.getAllByRole("heading", { level: 2 });
// 			expect(h2Elements.length).toBeGreaterThan(0);
// 		});

// 		it("has accessible buttons", async () => {
// 			renderWithQueryClient(<Todo />);

// 			await waitFor(() => {
// 				const buttons = screen.getAllByRole("button");
// 				for (const button of buttons) {
// 					expect(button).toHaveAccessibleName();
// 				}
// 			});
// 		});
// 	});
// });
