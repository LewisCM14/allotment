const getApiUrl = () => {
	// Prefer runtime config, fallback to Vite's env for local dev
	const configuredUrl =
		window.envConfig?.VITE_API_URL || import.meta.env.VITE_API_URL;

	if (
		typeof window !== "undefined" &&
		configuredUrl.startsWith("http:") &&
		window.location.protocol === "https:"
	) {
		return configuredUrl.replace("http:", "https:");
	}

	return configuredUrl;
};

export const API_VERSION =
	window.envConfig?.VITE_API_VERSION ||
	import.meta.env.VITE_API_VERSION ||
	"/api/v1";
export const API_URL = getApiUrl();
