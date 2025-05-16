/**
 * Error monitoring service
 * Captures and logs errors for debugging and monitoring
 */

interface ErrorContext {
	url?: string;
	method?: string;
	status?: number;
	[key: string]: unknown; // Changed from 'any' to 'unknown'
}

class ErrorMonitoringService {
	private isProduction = import.meta.env.PROD;
	private logEndpoint: string;

	constructor() {
		// Always use a fixed, relative path for the client error logging endpoint.
		// This ensures requests go to the frontend Nginx proxy, which then routes to the backend.
		// Assumes VITE_API_VERSION provides the correct version prefix like "/api/v1"
		// or defaults to a known one if that's also problematic.
		const apiVersionPath = import.meta.env.VITE_API_VERSION;

		if (typeof apiVersionPath === 'string' && apiVersionPath.startsWith('/')) {
			// Ensure apiVersionPath doesn't end with a slash to prevent double slashes
			const cleanedApiVersionPath = apiVersionPath.endsWith('/') ? apiVersionPath.slice(0, -1) : apiVersionPath;
			this.logEndpoint = `${cleanedApiVersionPath}/log-client-error`;
		} else {
			// Fallback if VITE_API_VERSION is not set or not in the expected format (e.g., /api/v1)
			console.warn(
				"VITE_API_VERSION environment variable is not optimally configured (expected e.g., '/api/v1'). Defaulting client error log endpoint to '/api/v1/log-client-error'. Ensure Nginx proxies this correctly."
			);
			this.logEndpoint = "/api/v1/log-client-error";
		}

		// Ensure the path starts with a single slash if it's relative.
		if (!this.logEndpoint.startsWith('/')) {
			this.logEndpoint = `/${this.logEndpoint}`;
		}

		if (this.isProduction) {
			console.log(`ErrorMonitoringService: logging to ${this.logEndpoint}`);
		}
	}

	captureException(error: unknown, context?: ErrorContext): void {
		if (!this.isProduction) {
			// Development logging
			console.error("[ErrorMonitor]", error, context);
			return;
		}

		try {
			// Prepare error data
			const errorData = {
				message: error instanceof Error ? error.message : String(error),
				stack: error instanceof Error ? error.stack : undefined,
				context,
				timestamp: new Date().toISOString(),
				url: window.location.href,
				userAgent: navigator.userAgent,
			};

			// Use non-blocking reporting
			if (navigator.sendBeacon) {
				const blob = new Blob([JSON.stringify(errorData)], {
					type: "application/json",
				});
				navigator.sendBeacon(this.logEndpoint, blob);
			} else {
				// Fallback to fetch with keepalive
				fetch(this.logEndpoint, {
					method: "POST",
					body: JSON.stringify(errorData),
					headers: {
						"Content-Type": "application/json",
					},
					keepalive: true,
				}).catch(() => {
					// Silently fail - don't let monitoring cause more errors
				});
			}
		} catch (e) {
			// Fail silently - monitoring should never break the app
		}
	}

	captureMessage(message: string, context?: ErrorContext): void {
		if (!this.isProduction) {
			console.info("[ErrorMonitor]", message, context);
			return;
		}

		try {
			// Similar to captureException but for informational messages
			const messageData = {
				message,
				level: "info",
				context,
				timestamp: new Date().toISOString(),
				url: window.location.href,
			};

			if (navigator.sendBeacon) {
				const blob = new Blob([JSON.stringify(messageData)], {
					type: "application/json",
				});
				navigator.sendBeacon(this.logEndpoint, blob);
			}
		} catch (e) {
			// Fail silently
		}
	}
}

export const errorMonitor = new ErrorMonitoringService();
