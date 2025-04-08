interface ServiceWorkerGlobalScope {
	readonly registration: ServiceWorkerRegistration;
	readonly caches: CacheStorage;
	skipWaiting(): Promise<void>;
	clients: Clients;

	// Add standard EventTarget methods
	addEventListener(
		type: string,
		listener: EventListenerOrEventListenerObject,
		options?: boolean | AddEventListenerOptions,
	): void;
	removeEventListener(
		type: string,
		listener: EventListenerOrEventListenerObject,
		options?: boolean | EventListenerOptions,
	): void;
	dispatchEvent(event: Event): boolean;
}

declare const self: ServiceWorkerGlobalScope;
declare const __WB_MANIFEST: Array<{ url: string; revision: string | null }>;
