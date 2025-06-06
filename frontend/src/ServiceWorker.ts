/// <reference lib="webworker" />
/// <reference path="./types/serviceWorkerTypes.ts" />
import { CacheableResponsePlugin } from "workbox-cacheable-response";
import { ExpirationPlugin } from "workbox-expiration";
import { precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";
import {
	CacheFirst,
	NetworkFirst,
	NetworkOnly,
	StaleWhileRevalidate,
} from "workbox-strategies";

declare const self: ServiceWorkerGlobalScope;

// Use the precache manifest generated by VitePWA
precacheAndRoute(self.__WB_MANIFEST);

const API_VERSION = import.meta.env.VITE_API_VERSION;

registerRoute(
	({ url }) =>
		url.pathname.startsWith(`${API_VERSION}/user/auth/`) ||
		url.pathname.startsWith(`${API_VERSION}/user/send-verification-email`) ||
		url.pathname.startsWith(`${API_VERSION}/user/verify-email`) ||
		url.pathname.startsWith(`${API_VERSION}/user/verification-status`),
	new NetworkOnly(),
);

// User profile data
registerRoute(
	({ url }) => url.pathname.startsWith(`${API_VERSION}/user/profile`),
	new StaleWhileRevalidate({
		cacheName: "user-data-cache",
		plugins: [
			new ExpirationPlugin({
				maxEntries: 10,
				maxAgeSeconds: 60 * 60 * 24 * 7, // 7 days
			}),
		],
	}),
);

// Botanical groups data
registerRoute(
	({ url }) => url.pathname === `${API_VERSION}/families/botanical-groups/`,
	new StaleWhileRevalidate({
		cacheName: "botanical-groups-cache",
		plugins: [
			new ExpirationPlugin({
				maxEntries: 18,
				maxAgeSeconds: 60 * 60 * 24 * 7, // 7 days
			}),
			new CacheableResponsePlugin({
				statuses: [0, 200],
			}),
		],
	}),
);

// Other API responses with network-first strategy
registerRoute(
	({ url }) => url.pathname.startsWith(API_VERSION),
	new NetworkFirst({
		cacheName: "api-cache",
		plugins: [
			new ExpirationPlugin({
				maxEntries: 50,
				maxAgeSeconds: 60 * 60 * 24, // 1 day
			}),
		],
	}),
);

// Cache assets
registerRoute(
	({ request }) =>
		request.destination === "image" || request.destination === "style",
	new CacheFirst({
		cacheName: "assets-cache",
		plugins: [
			new ExpirationPlugin({
				maxEntries: 60,
				maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
			}),
		],
	}),
);

// Static resources (scripts, styles)
registerRoute(
	({ request }) =>
		request.destination === "script" || request.destination === "style",
	new StaleWhileRevalidate({
		cacheName: "static-resources",
	}),
);

// Cache the fonts
registerRoute(
	({ request }) => request.destination === "font",
	new CacheFirst({
		cacheName: "font-cache",
		plugins: [
			new ExpirationPlugin({
				maxEntries: 10,
				maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
			}),
		],
	}),
);

// Fallback page for when offline and navigation fails
const navStrategy = new NetworkFirst({
	cacheName: "pages",
	plugins: [
		new CacheableResponsePlugin({ statuses: [200] }),
		new ExpirationPlugin({ maxEntries: 50 }),
	],
});

registerRoute(
	({ request }) => request.mode === "navigate",
	async ({ request, event }) => {
		try {
			const response = await navStrategy.handle({ request, event });
			if (response) return response;
			const index = await caches.match("/index.html");
			if (index) return index;
			return (
				(await caches.match("/offline.html")) ??
				new Response("Offline", { status: 503 })
			);
		} catch {
			return (
				(await caches.match("/offline.html")) ??
				new Response("Offline", { status: 503 })
			);
		}
	},
);

// Listen for message events - this allows communication with the main thread
self.addEventListener("message", (event) => {
	// Check if the message is about auth state
	if (event.data && event.data.type === "AUTH_STATE_CHANGE") {
		// Notify the main thread about the auth state change
		self.clients.matchAll({ includeUncontrolled: true }).then((clients) => {
			for (const client of clients) {
				client.postMessage({
					type: "AUTH_STATE_UPDATED",
					payload: event.data.payload,
				});
			}
		});
	}

	// Handle app update checks
	if (event.data && event.data.type === "SKIP_WAITING") {
		self.skipWaiting();
	}
});

// Add activate handler
self.addEventListener("activate", (event) => {
	event.waitUntil(self.clients.claim());
});

// Cache the app shell for offline use
self.addEventListener("install", (event) => {
	// take control immediately
	self.skipWaiting();

	const installEvent = event as ExtendableEvent;
	installEvent.waitUntil(
		caches.open("app-shell").then((cache) => {
			return cache.addAll([
				"/",
				"/index.html",
				"/offline.html",
				"/manifest.webmanifest", // <-- was /manifest.json
			]);
		}),
	);
});
