/**
 * Utilities for handling viewport height issues on mobile browsers,
 * particularly Safari where the URL bar affects the viewport height.
 */

/**
 * Sets CSS custom properties for accurate viewport height on mobile devices.
 * This function should be called on page load and window resize.
 */
export function setViewportHeight(): void {
	// Get the actual viewport height
	const vh = globalThis.innerHeight * 0.01;

	// Set CSS custom property for accurate vh calculation
	document.documentElement.style.setProperty("--vh", `${vh}px`);
}

/**
 * Initialize viewport height handling for mobile Safari compatibility.
 * Call this once when the app starts.
 */
export function initViewportHeight(): void {
	// Set initial viewport height
	setViewportHeight();

	// Update on resize (handles orientation changes and URL bar show/hide)
	globalThis.addEventListener("resize", setViewportHeight);

	// Also listen for orientationchange for better mobile support
	globalThis.addEventListener("orientationchange", () => {
		// Small delay to ensure the browser has finished the orientation change
		setTimeout(setViewportHeight, 100);
	});

	// Handle visual viewport API if available (for better Safari support)
	if (globalThis.visualViewport) {
		globalThis.visualViewport.addEventListener("resize", setViewportHeight);
	}
}

/**
 * Clean up viewport height event listeners.
 * Call this when unmounting the app.
 */
export function cleanupViewportHeight(): void {
	globalThis.removeEventListener("resize", setViewportHeight);
	globalThis.removeEventListener("orientationchange", setViewportHeight);

	if (globalThis.visualViewport) {
		globalThis.visualViewport.removeEventListener("resize", setViewportHeight);
	}
}
