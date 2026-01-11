/**
 * Lazy toast utility - defers sonner import until first toast is triggered.
 * This reduces initial bundle size by ~45KB for routes that don't immediately show toasts.
 */

export type ToastType = "success" | "error" | "info" | "warning" | "message";

interface ToastOptions {
	description?: string;
	duration?: number;
	id?: string | number;
	icon?: React.ReactNode;
	action?: {
		label: string;
		onClick: () => void;
	};
}

// Cache the toast module once loaded
let toastModule: typeof import("sonner") | null = null;
let loadingPromise: Promise<typeof import("sonner")> | null = null;

async function getToast() {
	if (toastModule) return toastModule;
	loadingPromise ??= import("sonner");
	toastModule = await loadingPromise;
	return toastModule;
}

/**
 * Show a toast notification. Lazily loads sonner on first use.
 */
export const lazyToast = {
	success: async (message: string, options?: ToastOptions) => {
		const { toast } = await getToast();
		return toast.success(message, options);
	},
	error: async (message: string, options?: ToastOptions) => {
		const { toast } = await getToast();
		return toast.error(message, options);
	},
	info: async (message: string, options?: ToastOptions) => {
		const { toast } = await getToast();
		return toast.info(message, options);
	},
	warning: async (message: string, options?: ToastOptions) => {
		const { toast } = await getToast();
		return toast.warning(message, options);
	},
	message: async (message: string, options?: ToastOptions) => {
		const { toast } = await getToast();
		return toast.message(message, options);
	},
	dismiss: async (toastId?: string | number) => {
		const { toast } = await getToast();
		return toast.dismiss(toastId);
	},
	promise: async <T>(
		promise: Promise<T>,
		options: {
			loading: string;
			success: string | ((data: T) => string);
			error: string | ((error: unknown) => string);
		},
	) => {
		const { toast } = await getToast();
		return toast.promise(promise, options);
	},
};

/**
 * Preload the toast module during idle time.
 * Call this after initial render to warm up the cache.
 */
export function preloadToast(): void {
	if (toastModule) return;

	const preload = () => {
		if (!loadingPromise) {
			loadingPromise = import("sonner");
			loadingPromise.then((module) => {
				toastModule = module;
			});
		}
	};

	if (window.requestIdleCallback) {
		window.requestIdleCallback(preload, { timeout: 2000 });
	} else {
		setTimeout(preload, 100);
	}
}
