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
	private logEndpoint =
		`${import.meta.env.VITE_API_URL}${import.meta.env.VITE_API_VERSION}/log-client-error`;

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
