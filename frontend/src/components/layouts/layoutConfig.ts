/**
 * Centralized layout configuration for responsive breakpoints and widths
 */

export type ScreenSize = "mobile" | "tablet" | "desktop";

export const breakpoints = {
	mobile: 0,
	tablet: 768,
	desktop: 1024,
};

export const containerWidths = {
	mobile: "96%",
	tablet: "84%",
	desktop: "66%",
};

export const toasterConfig = {
	mobile: {
		position: "bottom-center" as const,
		offset: 75,
		width: containerWidths.mobile,
	},
	tablet: {
		position: "bottom-right" as const,
		offset: 25,
		width: containerWidths.tablet,
	},
	desktop: {
		position: "bottom-right" as const,
		offset: 25,
		width: containerWidths.desktop,
	},
};

export const getScreenSize = (width: number): ScreenSize => {
	if (width < breakpoints.tablet) {
		return "mobile";
	}
	if (width < breakpoints.desktop) {
		return "tablet";
	}
	return "desktop";
};

// Convert container widths to Tailwind class strings
export const widthClasses = {
	default: `w-[${containerWidths.mobile}] md:w-[${containerWidths.tablet}] lg:w-[${containerWidths.desktop}]`,
};
