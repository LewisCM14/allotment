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

const getMessageFromDetail = (detail: unknown): string | null => {
	if (typeof detail === "string") {
		return detail;
	}
	if (Array.isArray(detail)) {
		return formatApiDetail(detail as Array<{ msg: string; loc: string[] }>);
	}
	if (detail && typeof detail === "object") {
		const obj = detail as { message?: unknown; msg?: unknown };
		if (typeof obj.message === "string") return obj.message;
		if (typeof obj.msg === "string") return obj.msg;
		return JSON.stringify(detail);
	}
	return null;
};

const handleErrorInstance = (error: Error): string => {
	if (error.message !== "[object Object]") {
		return error.message;
	}

	const err = error as { detail?: unknown; cause?: unknown };
	if (typeof err.detail === "string") {
		return err.detail;
	}

	if (err.cause) {
		const causeMessage = formatError(err.cause);
		const defaultMessage =
			"An error occurred, but its message was not properly formatted.";
		if (causeMessage !== "[object Object]" && causeMessage !== defaultMessage) {
			return causeMessage;
		}
	}

	return "An error occurred, but its message was not properly formatted.";
};

interface IObjectError {
	isAxiosError?: boolean;
	response?: { data?: unknown };
	message?: unknown;
	detail?: unknown;
	msg?: unknown;
}

const handleObjectError = (error: object): string => {
	const err = error as IObjectError;

	if (err.isAxiosError) {
		if (err.response?.data) return formatError(err.response.data);
		if (typeof err.message === "string") return err.message;
	}

	if ("detail" in err) {
		const detailMessage = getMessageFromDetail(err.detail);
		if (detailMessage) return detailMessage;
	}

	if (typeof err.message === "string") return err.message;
	if (typeof err.msg === "string") return err.msg;

	return JSON.stringify(error);
};

/**
 * Formats any error into a readable string message
 */
export const formatError = (error: unknown): string => {
	if (error instanceof Error) {
		return handleErrorInstance(error);
	}
	if (typeof error === "string") {
		return error;
	}
	if (error && typeof error === "object") {
		return handleObjectError(error);
	}
	return "An unexpected error occurred. Please try again.";
};
