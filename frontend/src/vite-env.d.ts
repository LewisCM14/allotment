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

declare module "worker:*" {
	const WorkerFactory: {
		new(url: string, options?: WorkerOptions): Worker;
	};
	export default WorkerFactory;
}

declare module "./utils/wsTracker.js" {
	const content: unknown;
	export default content;
}

declare module "*?worker" {
	const WorkerFactory: {
		new(): Worker;
	};
	export default WorkerFactory;
}
