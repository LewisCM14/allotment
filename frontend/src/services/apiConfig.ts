const getApiUrl = () => {
	const configuredUrl = import.meta.env.VITE_API_URL || "";

	if (
		typeof window !== "undefined" &&
		configuredUrl.startsWith("http:") &&
		window.location.protocol === "https:"
	) {
		return configuredUrl.replace("http:", "https:");
	}

	return configuredUrl;
};

export const API_VERSION = import.meta.env.VITE_API_VERSION;
export const API_URL = getApiUrl();
