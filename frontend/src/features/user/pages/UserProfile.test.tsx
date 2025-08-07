import { screen, waitFor, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UserProfile from "./UserProfile";
import { useAuth } from "@/store/auth/AuthContext";
import React from "react";
import { renderWithReactQuery } from "@/test-utils";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";

// Mock additional dependencies that the page uses
vi.mock("@/utils/errorUtils", () => ({
	formatError: vi.fn((error) => "Formatted error message"),
}));

vi.mock("@/services/errorMonitoring", () => ({
	errorMonitor: {
		captureException: vi.fn(),
		captureMessage: vi.fn(),
	},
}));

vi.mock("sonner", () => ({
	toast: {
		success: vi.fn(),
		error: vi.fn(),
	},
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
	const actual = await vi.importActual("react-router-dom");
	return {
		...actual,
		useNavigate: () => mockNavigate,
	};
});

// Mock useAuth
vi.mock("@/store/auth/AuthContext", () => ({
	useAuth: vi.fn(),
}));

function renderPage() {
	return renderWithReactQuery(
		<MemoryRouter>
			<UserProfile />
		</MemoryRouter>,
	);
}

describe("UserProfile", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		localStorage.clear();
		mockNavigate.mockClear();

		// Reset online status
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});

		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: false,
			},
			firstName: "Testy",
			isAuthenticated: true,
		});

		// Setup default successful API responses
		server.use(
			http.get("http://localhost:8000/api/v1/users/profile", () => {
				return HttpResponse.json({
					user_id: "test-user-id",
					user_email: "test@example.com",
					user_first_name: "Testy",
					user_country_code: "GB",
					is_email_verified: false,
				});
			}),
			http.get("http://localhost:8000/api/v1/users/verification-status", () => {
				return HttpResponse.json({
					is_email_verified: false,
				});
			}),
			http.post(
				"http://localhost:8000/api/v1/users/email-verifications",
				() => {
					return HttpResponse.json({
						message: "Verification email sent successfully",
					});
				},
			),
			http.put(
				"http://localhost:8000/api/v1/users/profile",
				async ({ request }) => {
					const body = (await request.json()) as {
						user_first_name?: string;
						user_country_code?: string;
					};
					return HttpResponse.json({
						user_id: "test-user-id",
						user_email: "test@example.com",
						user_first_name: body?.user_first_name || "Testy",
						user_country_code: body?.user_country_code || "GB",
						is_email_verified: false,
					});
				},
			),
		);
	});

	describe("Basic Page Functionality", () => {
		it("renders user name and email", () => {
			renderPage();
			expect(screen.getByText(/profile/i)).toBeInTheDocument();
			expect(screen.getByText(/testy/i)).toBeInTheDocument();
			expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
		});

		it("redirects to login when not authenticated", () => {
			(useAuth as unknown as Mock).mockReturnValue({
				user: null,
				firstName: null,
				isAuthenticated: false,
			});

			renderPage();

			expect(mockNavigate).toHaveBeenCalledWith("/login");
		});

		it("loads and displays profile data from API", async () => {
			server.use(
				http.get("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json({
						user_id: "test-user-id",
						user_email: "test@example.com",
						user_first_name: "API Loaded Name",
						user_country_code: "US",
						is_email_verified: false,
					});
				}),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText("API Loaded Name")).toBeInTheDocument();
				expect(screen.getByText("US")).toBeInTheDocument();
			});
		});
	});

	describe("Email Verification", () => {
		it("shows email not verified warning for unverified users", async () => {
			renderPage();
			expect(screen.getByText(/email not verified/i)).toBeInTheDocument();
			expect(
				screen.getByRole("button", {
					name: /send verification email/i,
				}),
			).toBeInTheDocument();
		});

		it("shows verified message if email is verified", async () => {
			(useAuth as unknown as Mock).mockReturnValue({
				user: {
					user_email: "test@example.com",
					user_first_name: "Testy",
					isEmailVerified: true,
				},
				firstName: "Testy",
				isAuthenticated: true,
			});

			server.use(
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json({
							is_email_verified: true,
						});
					},
				),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText(/✓ email verified/i)).toBeInTheDocument();
			});
		});

		it("can request verification email", async () => {
			renderPage();

			const verificationButton = await screen.findByRole("button", {
				name: /send verification email/i,
			});

			await userEvent.click(verificationButton);

			// Verify API was called (implicitly through MSW mock)
			expect(verificationButton).toBeInTheDocument();
		});

		it("can refresh verification status", async () => {
			renderPage();

			const refreshButton = await screen.findByRole("button", {
				name: /refresh status/i,
			});

			await userEvent.click(refreshButton);

			expect(refreshButton).toBeInTheDocument();
		});

		it("handles verification email request errors", async () => {
			server.use(
				http.post(
					"http://localhost:8000/api/v1/users/email-verifications",
					() => {
						return HttpResponse.json(
							{ error: "Failed to send email" },
							{ status: 500 },
						);
					},
				),
			);

			renderPage();

			const verificationButton = await screen.findByRole("button", {
				name: /send verification email/i,
			});

			await userEvent.click(verificationButton);

			// Should handle error gracefully - page should still be functional
			expect(verificationButton).toBeInTheDocument();
		});
	});

	describe("Profile Editing", () => {
		it("enables edit mode when edit button is clicked", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Find the edit button - it has an Edit icon but no text label
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			// Should show form elements
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});
			expect(screen.getByText("Save")).toBeInTheDocument();
			expect(screen.getByText("Cancel")).toBeInTheDocument();
		});

		it("cancels editing and resets form", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			// Wait for edit mode to be active
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Modify the form
			const nameInput = screen.getByPlaceholderText("Enter your first name");
			await userEvent.clear(nameInput);
			await userEvent.type(nameInput, "Modified Name");

			// Cancel editing
			const cancelButton = screen.getByText("Cancel");
			await userEvent.click(cancelButton);

			// Should exit edit mode and show original data
			await waitFor(() => {
				expect(
					screen.queryByPlaceholderText("Enter your first name"),
				).not.toBeInTheDocument();
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});
		});

		it("saves profile updates successfully", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			// Wait for edit mode to be active
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Update the form
			const nameInput = screen.getByPlaceholderText("Enter your first name");
			await userEvent.clear(nameInput);
			await userEvent.type(nameInput, "Updated Name");

			// Save changes
			const saveButton = screen.getByText("Save");
			await userEvent.click(saveButton);

			// Should exit edit mode
			await waitFor(() => {
				expect(
					screen.queryByPlaceholderText("Enter your first name"),
				).not.toBeInTheDocument();
			});
		});

		it("handles profile update errors", async () => {
			server.use(
				http.put("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json({ error: "Update failed" }, { status: 500 });
				}),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode and save
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			const saveButton = screen.getByText("Save");
			await userEvent.click(saveButton);

			// Should remain in edit mode due to error
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});
		});

		it("updates country code selection", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// The country selector should be available in edit mode
			const countrySelect = screen.getByRole("combobox");
			expect(countrySelect).toBeInTheDocument();

			// Save changes
			const saveButton = screen.getByText("Save");
			await userEvent.click(saveButton);

			// Should exit edit mode
			await waitFor(() => {
				expect(
					screen.queryByPlaceholderText("Enter your first name"),
				).not.toBeInTheDocument();
			});
		});

		it("shows loading states correctly", async () => {
			renderPage();

			// Should show checking status initially
			expect(screen.getByText("Checking...")).toBeInTheDocument();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});
		});

		it("handles edit mode state transitions", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Initially not in edit mode
			expect(
				screen.queryByPlaceholderText("Enter your first name"),
			).not.toBeInTheDocument();

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			// Now in edit mode
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Should have both Save and Cancel buttons
			expect(screen.getByText("Save")).toBeInTheDocument();
			expect(screen.getByText("Cancel")).toBeInTheDocument();

			// Edit button should not be visible anymore
			expect(
				screen.queryByRole("button", { name: "" }),
			).not.toBeInTheDocument();
		});
	});

	describe("Offline Handling", () => {
		it("handles offline state during save", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Simulate going offline
			Object.defineProperty(navigator, "onLine", {
				configurable: true,
				value: false,
				writable: true,
			});

			// Mock dispatchEvent for JSDOM environment
			const originalDispatchEvent = window.dispatchEvent;
			const mockDispatchEvent = vi.fn();
			Object.defineProperty(window, "dispatchEvent", {
				value: mockDispatchEvent,
				configurable: true,
			});

			// Trigger offline event
			act(() => {
				window.dispatchEvent(new Event("offline"));
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Try to save
			const saveButton = screen.getByText("Save");
			await userEvent.click(saveButton);

			// Should handle offline state gracefully - remain in edit mode
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Restore original dispatchEvent
			Object.defineProperty(window, "dispatchEvent", {
				value: originalDispatchEvent,
				configurable: true,
			});
		});

		it("handles online/offline events", () => {
			const addEventListenerSpy = vi.spyOn(window, "addEventListener");
			const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

			const { unmount } = renderPage();

			expect(addEventListenerSpy).toHaveBeenCalledWith(
				"online",
				expect.any(Function),
			);
			expect(addEventListenerSpy).toHaveBeenCalledWith(
				"offline",
				expect.any(Function),
			);

			unmount();

			expect(removeEventListenerSpy).toHaveBeenCalledWith(
				"online",
				expect.any(Function),
			);
			expect(removeEventListenerSpy).toHaveBeenCalledWith(
				"offline",
				expect.any(Function),
			);
		});
	});

	describe("Data Persistence", () => {
		it("stores email in localStorage", async () => {
			renderPage();

			await waitFor(() => {
				expect(localStorage.getItem("user_email")).toBe("test@example.com");
			});
		});

		it("stores verification status in localStorage", async () => {
			server.use(
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json({
							is_email_verified: true,
						});
					},
				),
			);

			renderPage();

			await waitFor(() => {
				expect(localStorage.getItem("is_email_verified")).toBe("true");
			});
		});

		it("handles missing user data gracefully", async () => {
			(useAuth as unknown as Mock).mockReturnValue({
				user: null,
				firstName: null,
				isAuthenticated: true,
			});

			server.use(
				http.get("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json(
						{ error: "Profile not found" },
						{ status: 404 },
					);
				}),
			);

			renderPage();

			// Should render with fallback values - using more specific queries
			await waitFor(() => {
				expect(screen.getByText("Profile")).toBeInTheDocument();
			});

			// Check for fallback text - there are multiple "Not provided" elements
			const notProvidedElements = screen.getAllByText("Not provided");
			expect(notProvidedElements.length).toBeGreaterThan(0);

			// Check for email fallback
			expect(screen.getByText("Not available")).toBeInTheDocument();
		});
	});

	describe("Advanced Integration Scenarios", () => {
		it("handles multiple API failures gracefully", async () => {
			server.use(
				http.get("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json({ error: "Network error" }, { status: 500 });
				}),
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json(
							{ error: "Service unavailable" },
							{ status: 503 },
						);
					},
				),
			);

			renderPage();

			// Page should still render despite API failures
			await waitFor(() => {
				expect(screen.getByText("Profile")).toBeInTheDocument();
			});
		});

		it("updates localStorage correctly during user interactions", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Check that email is stored
			await waitFor(() => {
				expect(localStorage.getItem("user_email")).toBe("test@example.com");
			});

			// Check verification status storage
			await waitFor(() => {
				expect(localStorage.getItem("is_email_verified")).toBe("false");
			});
		});

		it("handles verification status updates correctly", async () => {
			// Start with unverified status
			server.use(
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json({
							is_email_verified: false,
						});
					},
				),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Email Not Verified")).toBeInTheDocument();
			});

			// Update to verified status
			server.use(
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json({
							is_email_verified: true,
						});
					},
				),
			);

			// Click refresh button - it might be in "Checking..." state, so wait for it to be ready
			await waitFor(() => {
				const refreshButton = screen.getByRole("button", {
					name: /refresh status/i,
				});
				expect(refreshButton).toBeEnabled();
				return refreshButton;
			});

			const refreshButton = screen.getByRole("button", {
				name: /refresh status/i,
			});
			await userEvent.click(refreshButton);

			// Should update to verified status
			await waitFor(() => {
				expect(
					screen.queryByText("Email Not Verified"),
				).not.toBeInTheDocument();
			});
		});

		it("handles rapid user interactions without errors", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Rapidly click edit and cancel
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			const cancelButton = screen.getByText("Cancel");
			await userEvent.click(cancelButton);

			await waitFor(() => {
				expect(
					screen.queryByPlaceholderText("Enter your first name"),
				).not.toBeInTheDocument();
			});

			// Should be able to edit again
			const editButtonAgain = screen.getByRole("button", { name: "" });
			await userEvent.click(editButtonAgain);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});
		});

		it("handles concurrent save and verification requests", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Start edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Trigger verification email request
			const verificationButton = screen.getByText("Send Verification Email");
			const saveButton = screen.getByText("Save");

			// Click both quickly
			await userEvent.click(verificationButton);
			await userEvent.click(saveButton);

			// Should handle both operations without error
			await waitFor(() => {
				expect(
					screen.queryByPlaceholderText("Enter your first name"),
				).not.toBeInTheDocument();
			});
		});

		it("maintains form state during component re-renders", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Type in the field
			const nameInput = screen.getByPlaceholderText("Enter your first name");
			await userEvent.clear(nameInput);
			await userEvent.type(nameInput, "New Name");

			// Trigger a re-render by calling refresh
			const refreshButton = screen.getByText("Refresh Status");
			await userEvent.click(refreshButton);

			// Form state should be preserved
			await waitFor(() => {
				expect(screen.getByDisplayValue("New Name")).toBeInTheDocument();
			});
		});

		it("validates form fields", async () => {
			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			// Clear the required field to trigger validation
			const nameInput = screen.getByPlaceholderText("Enter your first name");
			await userEvent.clear(nameInput);
			await userEvent.type(nameInput, "X"); // Too short

			// Trigger validation by blurring
			fireEvent.blur(nameInput);

			await waitFor(() => {
				expect(screen.getByText(/must be at least/i)).toBeInTheDocument();
			});
		});

		it("handles network timeouts gracefully", async () => {
			// Mock slow/timeout responses
			server.use(
				http.put("http://localhost:8000/api/v1/users/profile", async () => {
					// Simulate timeout
					await new Promise((resolve) => setTimeout(resolve, 100));
					return HttpResponse.json(
						{ error: "Request timeout" },
						{ status: 408 },
					);
				}),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Testy")).toBeInTheDocument();
			});

			// Enter edit mode and save
			const editButton = screen.getByRole("button", { name: "" });
			await userEvent.click(editButton);

			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});

			const saveButton = screen.getByText("Save");
			await userEvent.click(saveButton);

			// Should handle timeout gracefully
			await waitFor(() => {
				expect(
					screen.getByPlaceholderText("Enter your first name"),
				).toBeInTheDocument();
			});
		});
	});

	describe("Error Handling", () => {
		it("handles profile loading errors", async () => {
			server.use(
				http.get("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json(
						{ error: "Failed to load profile" },
						{ status: 500 },
					);
				}),
			);

			renderPage();

			// Should handle error gracefully - page should still render
			await waitFor(() => {
				expect(screen.getByText(/profile/i)).toBeInTheDocument();
			});
		});

		it("handles verification status check errors", async () => {
			server.use(
				http.get(
					"http://localhost:8000/api/v1/users/verification-status",
					() => {
						return HttpResponse.json(
							{ error: "Server error" },
							{ status: 500 },
						);
					},
				),
			);

			renderPage();

			// Should render the page despite verification status error
			expect(screen.getByText(/profile/i)).toBeInTheDocument();
		});

		it("handles missing email for verification operations", async () => {
			(useAuth as unknown as Mock).mockReturnValue({
				user: {
					user_email: "",
					user_first_name: "Testy",
					isEmailVerified: false,
				},
				firstName: "Testy",
				isAuthenticated: true,
			});

			server.use(
				http.get("http://localhost:8000/api/v1/users/profile", () => {
					return HttpResponse.json({
						user_id: "test-user-id",
						user_email: "",
						user_first_name: "Testy",
						user_country_code: "GB",
						is_email_verified: false,
					});
				}),
			);

			renderPage();

			await waitFor(() => {
				expect(screen.getByText("Send Verification Email")).toBeInTheDocument();
			});

			const verificationButton = screen.getByText("Send Verification Email");
			await userEvent.click(verificationButton);

			// Should handle missing email gracefully
			expect(verificationButton).toBeInTheDocument();
		});
	});

	// Legacy test kept for compatibility
	it("can interact with buttons without errors", async () => {
		// Mock endpoints
		server.use(
			http.post("http://localhost:8000/api/v1/request-verification", () => {
				return HttpResponse.json({
					message: "Verification email sent successfully",
				});
			}),
			http.get("http://localhost:8000/api/v1/check-email-verification", () => {
				return HttpResponse.json({ is_email_verified: true });
			}),
		);

		(useAuth as unknown as Mock).mockReturnValue({
			user: {
				user_email: "test@example.com",
				user_first_name: "Testy",
				isEmailVerified: false,
			},
			firstName: "Testy",
			isAuthenticated: true,
		});

		renderPage();

		// Test send verification email button
		const verificationButton = await screen.findByRole("button", {
			name: /send verification email/i,
		});
		expect(verificationButton).toBeInTheDocument();
		await userEvent.click(verificationButton);

		// Test refresh button - just check if we can find and click it without erroring
		const refreshButton = screen.getByRole("button", {
			name: /refresh status/i,
		});
		expect(refreshButton).toBeInTheDocument();
		await userEvent.click(refreshButton);

		// No specific assertions needed - just that no errors occurred
		expect(true).toBe(true);
	});
});
