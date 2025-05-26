interface IServiceWorkerGlobalScope {
	readonly registration: ServiceWorkerRegistration;
	readonly caches: CacheStorage;
	skipWaiting(): Promise<void>;
	clients: Clients;

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

declare const __WB_MANIFEST: Array<{ url: string; revision: string | null }>;
