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
		if (error.message === "[object Object]") {
			if (
				"detail" in error &&
				typeof (error as { detail: unknown }).detail === "string"
			) {
				return (error as { detail: string }).detail;
			}
			if ("cause" in error && (error as { cause: unknown }).cause) {
				const causeMessage = formatError((error as { cause: unknown }).cause);
				if (
					causeMessage !== "[object Object]" &&
					causeMessage !==
						"An error occurred, but its message was not properly formatted."
				) {
					return causeMessage;
				}
			}
			return "An error occurred, but its message was not properly formatted.";
		}
		return error.message;
	}

	if (typeof error === "string") {
		return error;
	}

	interface AxiosErrorLike {
		isAxiosError?: boolean;
		response?: { data?: unknown };
		message?: string;
	}

	if (error && typeof error === "object") {
		const axiosError = error as AxiosErrorLike;
		if (
			axiosError.isAxiosError &&
			axiosError.response &&
			axiosError.response.data
		) {
			return formatError(axiosError.response.data);
		}
		if (axiosError.isAxiosError && axiosError.message) {
			return axiosError.message;
		}
		if ("detail" in error) {
			const detail = (error as { detail: unknown }).detail;
			if (typeof detail === "string") {
				return detail;
			}
			if (Array.isArray(detail)) {
				return formatApiDetail(detail as Array<{ msg: string; loc: string[] }>);
			}
			if (detail && typeof detail === "object") {
				if (
					"message" in detail &&
					typeof (detail as { message: unknown }).message === "string"
				) {
					return (detail as { message: string }).message;
				}
				if (
					"msg" in detail &&
					typeof (detail as { msg: unknown }).msg === "string"
				) {
					return (detail as { msg: string }).msg;
				}
				return JSON.stringify(detail);
			}
		}

		if (
			"message" in error &&
			typeof (error as { message: unknown }).message === "string"
		) {
			return (error as { message: string }).message;
		}
		if ("msg" in error && typeof (error as { msg: unknown }).msg === "string") {
			return (error as { msg: string }).msg;
		}

		return JSON.stringify(error);
	}

	return "An unexpected error occurred. Please try again.";
};
