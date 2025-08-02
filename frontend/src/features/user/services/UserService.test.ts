import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildUrl } from "../../../mocks/buildUrl";
import { server } from "../../../mocks/server";
import api from "../../../services/api";
import {
	checkEmailVerificationStatus,
	requestPasswordReset,
	requestVerificationEmail,
	resetPassword,
	verifyEmail,
} from "./UserService";

describe("UserService", () => {
	beforeEach(() => {
		Object.defineProperty(navigator, "onLine", {
			configurable: true,
			value: true,
			writable: true,
		});
		localStorage.clear();
		vi.restoreAllMocks();
	});

	afterEach(() => {
		server.resetHandlers();
	});

	describe("requestVerificationEmail", () => {
		it("should send a verification email successfully", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications"),
					async ({ request }) => {
						const body = (await request.json()) as { user_email?: string };
						if (body.user_email === "test@example.com") {
							return HttpResponse.json({ message: "Verification email sent" });
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			const result = await requestVerificationEmail("test@example.com");
			expect(result).toEqual({ message: "Verification email sent" });
		});

		it("should handle email not found error (404)", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications"),
					async ({ request }) => {
						const body = (await request.json()) as { user_email?: string };
						if (body.user_email === "nonexistent@example.com") {
							return HttpResponse.json(
								{ detail: "Email address not found" },
								{ status: 404 },
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestVerificationEmail("nonexistent@example.com"),
			).rejects.toThrow("Email address not found");
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Invalid email format" }] },
						{ status: 422 },
					);
				}),
			);
			await expect(requestVerificationEmail("invalid-email")).rejects.toThrow(
				"Invalid email format",
			);
		});

		it("should handle service unavailable (503)", async () => {
			const postSpy = vi.spyOn(api, "post");
			const serviceUnavailableError = new Error("Service Unavailable");
			Object.defineProperty(serviceUnavailableError, "isAxiosError", {
				value: true,
			});
			Object.defineProperty(serviceUnavailableError, "response", {
				value: {
					status: 503,
					data: { detail: "Service down" },
				},
			});
			postSpy.mockRejectedValueOnce(serviceUnavailableError);

			await expect(
				requestVerificationEmail("test@example.com"),
			).rejects.toThrow("Service down");
			postSpy.mockRestore();
		});
	});

	describe("verifyEmail", () => {
		it("should verify email successfully when not from reset", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params, request }) => {
						const url = new URL(request.url);
						const fromReset = url.searchParams.get("fromReset") === "true";
						if (params.token === "valid-token") {
							return HttpResponse.json({
								message: fromReset
									? "Email verified successfully. You can now reset your password."
									: "Email verified successfully",
							});
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
			);
			const result = await verifyEmail("valid-token", false);
			expect(result).toEqual({ message: "Email verified successfully" });
		});

		it("should verify email successfully when from reset", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params, request }) => {
						const url = new URL(request.url);
						const fromReset = url.searchParams.get("fromReset") === "true";
						if (params.token === "valid-token-for-reset") {
							return HttpResponse.json({
								message: fromReset
									? "Email verified successfully. You can now reset your password."
									: "Email verified successfully",
							});
						}
					},
				),
			);
			const result = await verifyEmail("valid-token-for-reset", true);
			expect(result).toEqual({
				message:
					"Email verified successfully. You can now reset your password.",
			});
		}, 10000);

		it("should handle invalid verification token (400)", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					async ({ params }) => {
						if (params.token === "invalid-token") {
							return HttpResponse.json(
								{ detail: "Invalid verification token" },
								{ status: 400 },
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("invalid-token")).rejects.toThrow(
				"Invalid verification token",
			);
		});

		it("should handle invalid verification token (404)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications/:token"), () => {
					return HttpResponse.json(
						{ detail: "Token not found" },
						{ status: 404 },
					);
				}),
			);
			await expect(verifyEmail("not-found-token")).rejects.toThrow(
				"Token not found",
			);
		});

		it("should handle expired verification token", async () => {
			server.use(
				http.post(
					buildUrl("/users/email-verifications/:token"),
					({ params }) => {
						if (params.token === "expired-token") {
							return HttpResponse.json(
								{ detail: "Token has expired" },
								{ status: 410 },
							);
						}
						return HttpResponse.json(
							{ detail: "Unhandled mock" },
							{ status: 500 },
						);
					},
				),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("expired-token")).rejects.toThrow(
				"Token has expired",
			);
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/email-verifications/:token"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Validation issue" }] },
						{ status: 422 },
					);
				}),
				http.options(buildUrl("/users/email-verifications/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(verifyEmail("any-token")).rejects.toThrow(
				"Validation issue",
			);
		});
	});

	describe("requestPasswordReset", () => {
		it("should request password reset successfully if user exists and is verified", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), async ({ request }) => {
					const body = (await request.json()) as { user_email?: string };
					if (body.user_email === "verified@example.com") {
						return HttpResponse.json({ message: "Reset email sent" });
					}
					return HttpResponse.json(
						{ detail: "Unhandled mock" },
						{ status: 500 },
					);
				}),
			);
			await expect(
				requestPasswordReset("verified@example.com"),
			).resolves.toEqual({
				message: "Reset email sent",
			});
		});

		it("should handle email not found (404) as per current frontend logic", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: "Email address not found. Please check and try again." },
						{ status: 404 },
					);
				}),
				http.options(buildUrl("/users/password-resets"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestPasswordReset("nonexistent@example.com"),
			).rejects.toThrow("Email address not found. Please check and try again.");
		});

		it("should handle email not verified (400) as per current frontend logic", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: "Email not verified" },
						{ status: 400 },
					);
				}),
				http.options(buildUrl("/users/password-resets"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(
				requestPasswordReset("unverified@example.com"),
			).rejects.toThrow("Email not verified");
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(buildUrl("/users/password-resets"), () => {
					return HttpResponse.json(
						{ detail: [{ msg: "Invalid email for reset" }] },
						{ status: 422 },
					);
				}),
			);
			await expect(requestPasswordReset("bad-email@format")).rejects.toThrow(
				"Invalid email for reset",
			);
		});

		it("should handle service unavailable (503)", async () => {
			const postSpy = vi.spyOn(api, "post");
			const serviceUnavailableError = new Error("Service Unavailable");
			Object.defineProperty(serviceUnavailableError, "isAxiosError", {
				value: true,
			});
			Object.defineProperty(serviceUnavailableError, "response", {
				value: {
					status: 503,
					data: { detail: "Email service down" },
				},
			});
			postSpy.mockRejectedValueOnce(serviceUnavailableError);

			await expect(requestPasswordReset("any@example.com")).rejects.toThrow(
				"Email service down",
			);
			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(api, "post");
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(requestPasswordReset("user@example.com")).rejects.toThrow(
				"Network error. Please check your connection and try again.",
			);
			postSpy.mockRestore();
		});
	});

	describe("resetPassword", () => {
		it("should reset password successfully", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params, request }) => {
						const body = (await request.json()) as {
							new_password?: string;
						};
						if (
							params.token === "valid-token" &&
							body.new_password === "NewPass123!"
						) {
							return HttpResponse.json({ message: "Password updated" });
						}
						return HttpResponse.json(
							{ detail: "Invalid token" },
							{ status: 400 },
						);
					},
				),
			);
			await expect(
				resetPassword("valid-token", "NewPass123!"),
			).resolves.toEqual({
				message: "Password updated",
			});
		});

		it("should handle invalid or expired token (400)", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params }) => {
						if (params.token === "bad-token") {
							return HttpResponse.json(
								{ detail: "Invalid token" },
								{ status: 400 },
							);
						}
						return HttpResponse.json({ message: "Password updated" });
					},
				),
				http.options(buildUrl("/users/password-resets/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(resetPassword("bad-token", "NewPass123!")).rejects.toThrow(
				"Invalid token",
			);
		});

		it("should handle validation errors (422)", async () => {
			server.use(
				http.post(
					buildUrl("/users/password-resets/:token"),
					async ({ params, request }) => {
						const body = (await request.json()) as {
							new_password?: string;
						};
						if (
							params.token === "valid-token" &&
							body.new_password === "short"
						) {
							return HttpResponse.json(
								{
									detail: [{ loc: ["body", "new_password"], msg: "Too weak" }],
								},
								{ status: 422 },
							);
						}
						return HttpResponse.json({ message: "Password updated" });
					},
				),
				http.options(buildUrl("/users/password-resets/:token"), () => {
					return new HttpResponse(null, { status: 204 });
				}),
			);
			await expect(resetPassword("valid-token", "short")).rejects.toThrow(
				/Too weak/,
			);
		});

		it("should handle server errors (500)", async () => {
			const postSpy = vi.spyOn(api, "post");
			const err = new Error("Server down");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "response", {
				value: { status: 500, data: {} },
			});
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				"Server error. Please try again later.",
			);
			postSpy.mockRestore();
		});

		it("should handle network errors", async () => {
			const postSpy = vi.spyOn(api, "post");
			const err = new Error("Network Error");
			Object.defineProperty(err, "isAxiosError", { value: true });
			Object.defineProperty(err, "request", { value: {} });
			Object.defineProperty(err, "response", { value: undefined });
			postSpy.mockRejectedValueOnce(err);
			await expect(resetPassword("any-token", "NewPass123!")).rejects.toThrow(
				"Network error. Please check your connection and try again.",
			);
			postSpy.mockRestore();
		});
	});

	describe("checkEmailVerificationStatus", () => {
		it("should return true if email is verified", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					if (url.searchParams.get("user_email") === "verified@example.com") {
						return HttpResponse.json({ is_email_verified: true });
					}
					return HttpResponse.json({ detail: "Not found" }, { status: 404 });
				}),
			);

			const result = await checkEmailVerificationStatus("verified@example.com");
			expect(result).toEqual({ is_email_verified: true });
		});

		it("should return false if email is not verified", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), ({ request }) => {
					const url = new URL(request.url);
					if (
						url.searchParams.get("user_email") === "notverified@example.com"
					) {
						return HttpResponse.json({ is_email_verified: false });
					}
					return HttpResponse.json({ detail: "Not found" }, { status: 404 });
				}),
			);

			const result = await checkEmailVerificationStatus(
				"notverified@example.com",
			);
			expect(result).toEqual({ is_email_verified: false });
		});

		it("should throw EMAIL_NOT_FOUND if user email is not found (404)", async () => {
			server.use(
				http.get(buildUrl("/users/verification-status"), () => {
					return HttpResponse.json({ detail: "Not Found" }, { status: 404 });
				}),
			);

			await expect(
				checkEmailVerificationStatus("unknown@example.com"),
			).rejects.toThrow("Not Found");
		});

		it("should throw SERVER_ERROR for other server errors", async () => {
			await expect(
				checkEmailVerificationStatus("server-error@example.com"),
			).rejects.toThrow("Server error. Please try again later.");
		}, 10000);

		it("should throw NETWORK_ERROR for network errors", async () => {
			const getSpy = vi.spyOn(api, "get");
			const networkError = new Error("Network Error");
			Object.defineProperty(networkError, "isAxiosError", { value: true });
			Object.defineProperty(networkError, "request", { value: {} });
			getSpy.mockRejectedValueOnce(networkError);

			await expect(
				checkEmailVerificationStatus("test@example.com"),
			).rejects.toThrow(
				"Network error. Please check your connection and try again.",
			);
			getSpy.mockRestore();
		});
	});
});
