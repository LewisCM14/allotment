/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
/// <reference types="@testing-library/jest-dom" />

interface EnvConfig {
	VITE_APP_TITLE?: string;
	VITE_API_URL?: string;
	VITE_API_VERSION?: string;
	VITE_CONTACT_EMAIL?: string;
	VITE_FORCE_AUTH?: string;
	[key: string]: string | undefined; // Index signature for dynamic access
}

declare global {
	interface Window {
		envConfig?: EnvConfig;
	}
}

declare module "*.png*" {
	const src: string;
	export default src;
}
declare module "*.jpg*" {
	const src: string;
	export default src;
}
declare module "*.jpeg*" {
	const src: string;
	export default src;
}
declare module "*.webp*" {
	const src: string;
	export default src;
}
declare module "*.avif*" {
	const src: string;
	export default src;
}

declare module "./utils/wsTracker" {
	const content: unknown;
	export default content;
}

export {};
