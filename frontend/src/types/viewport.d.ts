/**
 * Type definitions for Visual Viewport API
 * This extends the global Window interface to include the visualViewport property
 */

interface VisualViewport extends EventTarget {
	readonly height: number;
	readonly width: number;
	readonly offsetLeft: number;
	readonly offsetTop: number;
	readonly pageLeft: number;
	readonly pageTop: number;
	readonly scale: number;
	addEventListener(type: "resize", listener: () => void): void;
	addEventListener(type: "scroll", listener: () => void): void;
	removeEventListener(type: "resize", listener: () => void): void;
	removeEventListener(type: "scroll", listener: () => void): void;
}

declare global {
	interface Window {
		visualViewport?: VisualViewport;
	}
}

export {};
