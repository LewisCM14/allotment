/**
 * Route prefetching utilities for improved perceived performance.
 * Uses dynamic imports to preload route chunks before navigation.
 */

// Route chunk importers - mirrors the lazy imports in AppRoutes.tsx
const routeChunks = {
	// Protected routes
	todo: () => import("../features/todo/pages/Todo"),
	growGuides: () => import("../features/grow_guide/pages/GrowGuides"),
	botanicalGroups: () => import("../features/family/pages/BotanicalGroups"),
	familyInfo: () => import("../features/family/pages/FamilyInfo"),
	allotment: () => import("../features/allotment/pages/UserAllotmentInfo"),
	preferences: () => import("../features/preference/pages/UserPreference"),
	profile: () => import("../features/user/pages/UserProfile"),

	// Public routes
	login: () => import("../features/auth/forms/LoginForm"),
	register: () => import("../features/registration/forms/RegisterForm"),
	resetPassword: () => import("../features/auth/forms/ResetPassword"),
	setNewPassword: () => import("../features/auth/forms/SetNewPassword"),
	publicGrowGuides: () =>
		import("../features/grow_guide/pages/PublicGrowGuides"),
	emailVerification: () =>
		import("../features/registration/pages/EmailVerification"),
} as const;

export type RouteName = keyof typeof routeChunks;

// Track which routes have been prefetched to avoid duplicate work
const prefetchedRoutes = new Set<RouteName>();

/**
 * Prefetch a single route chunk using requestIdleCallback for non-blocking load.
 * Falls back to setTimeout for browsers without requestIdleCallback support.
 */
export function prefetchRoute(route: RouteName): void {
	if (prefetchedRoutes.has(route)) {
		return;
	}

	const doPrefetch = () => {
		prefetchedRoutes.add(route);
		routeChunks[route]().catch(() => {
			// Silent fail - prefetch is best-effort optimization
			prefetchedRoutes.delete(route);
		});
	};

	if (window.requestIdleCallback) {
		window.requestIdleCallback(doPrefetch, { timeout: 3000 });
	} else {
		setTimeout(doPrefetch, 100);
	}
}

/**
 * Prefetch multiple route chunks.
 * Spaces out the imports to avoid network congestion.
 */
export function prefetchRoutes(routes: RouteName[]): void {
	routes.forEach((route, index) => {
		// Stagger prefetches by 100ms to avoid blocking critical requests
		setTimeout(() => prefetchRoute(route), index * 100);
	});
}

/**
 * Prefetch routes likely to be needed after login.
 * Called from login page during idle time.
 */
export function prefetchPostLoginRoutes(): void {
	prefetchRoutes(["todo", "growGuides", "profile"]);
}

/**
 * Prefetch routes likely to be needed from the dashboard.
 * Called from Todo page during idle time.
 */
export function prefetchDashboardRoutes(): void {
	prefetchRoutes(["growGuides", "botanicalGroups", "preferences"]);
}

/**
 * Prefetch a route on hover/focus for instant navigation.
 * Use with nav links for near-instant perceived navigation.
 */
export function prefetchOnInteraction(route: RouteName): () => void {
	return () => prefetchRoute(route);
}

/**
 * Map of route paths to their prefetch handlers.
 * Used for programmatic prefetching based on URL patterns.
 */
export const routePathMap: Record<string, RouteName> = {
	"/": "todo",
	"/grow-guides": "growGuides",
	"/botanical_groups": "botanicalGroups",
	"/allotment": "allotment",
	"/preferences": "preferences",
	"/profile": "profile",
	"/login": "login",
	"/register": "register",
	"/public-guides": "publicGrowGuides",
	"/public/grow-guides": "publicGrowGuides",
};

/**
 * Prefetch route by its URL path.
 */
export function prefetchByPath(path: string): void {
	const route = routePathMap[path];
	if (route) {
		prefetchRoute(route);
	}
}
