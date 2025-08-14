/**
 * Retrieves an environment variable.
 * Prioritizes runtime configuration from `window.envConfig` (loaded from env-config.js),
 * then falls back to build-time environment variables from `import.meta.env`.
 *
 * @param key The environment variable key (e.g., "VITE_API_URL").
 * @param defaultValue An optional default value if the variable is not found.
 * @returns The value of the environment variable or the default value.
 */
const getEnvVariable = (
	key: string,
	defaultValue?: string,
): string | undefined => {
	const runtimeVar =
		typeof window !== "undefined" ? window.envConfig?.[key] : undefined;
	const buildTimeVar =
		import.meta.env?.[key] != null ? String(import.meta.env[key]) : undefined;

	return runtimeVar ?? buildTimeVar ?? defaultValue;
};

// --- API URL Configuration ---
let configuredUrl = getEnvVariable("VITE_API_URL", "http://localhost:8000"); // Default for local dev if nothing is set

if (!configuredUrl) {
	const msg =
		"VITE_API_URL is not defined. Defaulting to 'http://localhost:8000'. Check your .env files or runtime environment configuration.";
	if (import.meta.env.PROD) {
		// Lazy import to avoid circular dependency
		const { errorMonitor } = require("@/services/errorMonitoring");
		errorMonitor.captureMessage(msg, { context: "apiConfig_missing_api_url" });
	} else {
		console.warn(msg);
	}
	configuredUrl = "http://localhost:8000"; // Failsafe default
}

// Automatically upgrade to HTTPS if the site is served over HTTPS but API URL is HTTP
// This prevents mixed content errors.
const getApiUrl = (): string => {
	let url = configuredUrl;
	if (
		typeof window !== "undefined" &&
		url.startsWith("http:") &&
		window.location.protocol === "https:"
	) {
		url = url.replace("http:", "https:");
	}
	// Ensure no trailing slash for consistency
	return url.endsWith("/") ? url.slice(0, -1) : url;
};

export const API_URL = getApiUrl();

// --- API Version Configuration ---
let configuredApiVersion = getEnvVariable("VITE_API_VERSION", "/api/v1");

if (!configuredApiVersion) {
	const msg =
		"VITE_API_VERSION is not defined. Defaulting to '/api/v1'. Check your .env files or runtime environment configuration.";
	if (import.meta.env.PROD) {
		// Lazy import to avoid circular dependency
		const { errorMonitor } = require("@/services/errorMonitoring");
		errorMonitor.captureMessage(msg, {
			context: "apiConfig_missing_api_version",
		});
	} else {
		console.warn(msg);
	}
	configuredApiVersion = "/api/v1"; // Failsafe default
}

// Ensure API_VERSION starts with a slash and has no trailing slash for consistency
const formatApiVersion = (version: string): string => {
	let formattedVersion = version;
	if (!formattedVersion.startsWith("/")) {
		formattedVersion = `/${formattedVersion}`;
	}
	if (formattedVersion.endsWith("/")) {
		formattedVersion = formattedVersion.slice(0, -1);
	}
	return formattedVersion;
};

export const API_VERSION = formatApiVersion(configuredApiVersion);
