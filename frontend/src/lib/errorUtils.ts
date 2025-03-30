/**
 * Formats an API error detail to a string, handling both string and array formats.
 */
export const formatApiDetail = (
	detail: string | Array<{ msg: string; loc: string[] }>,
): string => {
	if (typeof detail === "string") {
		return detail;
	}

	if (Array.isArray(detail)) {
		return detail.map((err) => err.msg).join(", ");
	}

	return "Unknown error";
};

/**
 * Formats any error into a readable string message
 */
export const formatError = (error: unknown): string => {
	if (error instanceof Error) {
		return error.message;
	}

	if (typeof error === "string") {
		return error;
	}

	// For objects with detail field (like our API errors)
	if (error && typeof error === "object" && "detail" in error) {
		const detail = (error as { detail: unknown }).detail;

		if (typeof detail === "string") {
			return detail;
		}

		if (Array.isArray(detail)) {
			// Fixed the 'any' type by providing a proper type assertion
			return formatApiDetail(detail as Array<{ msg: string; loc: string[] }>);
		}
	}

	return "An unexpected error occurred. Please try again.";
};
