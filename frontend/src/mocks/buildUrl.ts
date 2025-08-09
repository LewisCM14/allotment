import { API_URL, API_VERSION } from "../services/apiConfig";

export const buildUrl = (path: string) => {
	const apiVersionSegment = API_VERSION.startsWith("/")
		? API_VERSION
		: `/${API_VERSION}`;
	const pathSegment = path.startsWith("/") ? path : `/${path}`;
	return `${API_URL}${apiVersionSegment}${pathSegment}`.replace(
		/([^:]\/)\/+/g,
		"$1",
	);
};
