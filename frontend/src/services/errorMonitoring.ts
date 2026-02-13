/**
 * Error monitoring service
 * Captures and logs errors for debugging and monitoring
 */

interface IErrorContext {
	url?: string;
	method?: string;
	status?: number;
	[key: string]: unknown;
}

class ErrorMonitoringService {
	private _logEndpoint?: string;

	private get logEndpoint(): string {
		if (!this._logEndpoint) {
			// Lazy import to avoid circular dependency with apiConfig
			const { API_VERSION } = require("./apiConfig");
			const apiVersionPath = API_VERSION;

			if (
				typeof apiVersionPath === "string" &&
				apiVersionPath.startsWith("/")
			) {
				const cleanedApiVersionPath = apiVersionPath.endsWith("/")
					? apiVersionPath.slice(0, -1)
					: apiVersionPath;
				this._logEndpoint = `${cleanedApiVersionPath}/log-client-error`;
			} else {
				if (!import.meta.env.PROD) {
					console.warn(
						"VITE_API_VERSION environment variable is not optimally configured (expected e.g., '/api/v1'). Defaulting client error log endpoint to '/api/v1/log-client-error'. Ensure Nginx proxies this correctly.",
					);
				}
				this._logEndpoint = "/api/v1/log-client-error";
			}
		}
		return this._logEndpoint;
	}

	captureException(error: unknown, context?: IErrorContext): void {
		if (!import.meta.env.PROD) {
			// For easier test migration, match legacy signature if context is present
			if (context?.context === "loadAuthFromIndexedDB") {
				console.error("Error loading auth from IndexedDB:", error);
			} else {
				console.error("[ErrorMonitor]", error, context);
			}
			return;
		}

		try {
			const errorData = {
				error: error instanceof Error ? error.message : String(error),
				details: {
					stack: error instanceof Error ? error.stack : undefined,
					context,
					timestamp: new Date().toISOString(),
					url: globalThis.location.href,
					userAgent: navigator.userAgent,
				},
			};

			if (navigator.sendBeacon) {
				const blob = new Blob([JSON.stringify(errorData)], {
					type: "application/json",
				});
				navigator.sendBeacon(this.logEndpoint, blob);
			} else {
				fetch(this.logEndpoint, {
					method: "POST",
					body: JSON.stringify(errorData),
					headers: {
						"Content-Type": "application/json",
					},
					keepalive: true,
				}).catch((fetchError) => {
					// Log fetch errors locally if we're not in production
					if (!import.meta.env.PROD) {
						console.error(
							"[ErrorMonitor] Failed to send error data:",
							fetchError,
						);
					}
				});
			}
		} catch (e) {
			// Log internal error handling failures, but only in non-production
			if (!import.meta.env.PROD) {
				console.error("[ErrorMonitor] Error in error handling:", e);
			}
		}
	}

	captureMessage(message: string, context?: IErrorContext): void {
		if (!import.meta.env.PROD) {
			// For easier test migration, match legacy signature if context is present
			if (context?.context === "loadAuthFromIndexedDB") {
				console.info("Error loading auth from IndexedDB:", message);
			} else {
				console.info("[ErrorMonitor]", message, context);
			}
			return;
		}

		try {
			const messageData = {
				error: message,
				details: {
					level: "info",
					context,
					timestamp: new Date().toISOString(),
					url: globalThis.location.href,
					userAgent: navigator.userAgent,
				},
			};

			if (navigator.sendBeacon) {
				const blob = new Blob([JSON.stringify(messageData)], {
					type: "application/json",
				});
				navigator.sendBeacon(this.logEndpoint, blob);
			} else {
				fetch(this.logEndpoint, {
					method: "POST",
					body: JSON.stringify(messageData),
					headers: {
						"Content-Type": "application/json",
					},
					keepalive: true,
				}).catch((fetchError) => {
					// Log fetch errors locally if we're not in production
					if (!import.meta.env.PROD) {
						console.error(
							"[ErrorMonitor] Failed to send message data:",
							fetchError,
						);
					}
				});
			}
		} catch (e) {
			// Log internal error handling failures, but only in non-production
			if (!import.meta.env.PROD) {
				console.error("[ErrorMonitor] Error in message handling:", e);
			}
		}
	}
}

export const errorMonitor = new ErrorMonitoringService();
