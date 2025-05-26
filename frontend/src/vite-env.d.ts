/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

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

declare module "./utils/wsTracker.js" {
	const content: unknown;
	export default content;
}

interface EnvConfig {
	VITE_APP_TITLE: string;
	VITE_API_URL: string;
	VITE_API_VERSION: string;
	VITE_CONTACT_EMAIL: string;
	VITE_FORCE_AUTH: string; // Stored as string, parse to boolean in code
}

interface Window {
	envConfig: EnvConfig;
}
