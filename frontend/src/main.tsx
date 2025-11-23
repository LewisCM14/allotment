import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Suspense, lazy, useEffect, StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./global.css";
import { ThemeProvider } from "./store/theme/ThemeProvider";

const App = lazy(() => import("./App"));

const onOfflineReady = () => {
	import("sonner").then(({ toast }) =>
		toast.success("App ready to work offline", {
			description: "You can use the app even without an internet connection",
			duration: 3000,
		}),
	);
};

const handlePwaRegistration = () => {
	import("virtual:pwa-register").then(({ registerSW }) => {
		const updateSW = registerSW({
			onNeedRefresh() {
				if (confirm("New content available. Reload?")) {
					updateSW();
				}
			},
			onOfflineReady,
		});
	});
};

function Main() {
	useEffect(() => {
		const loadWs = () => import("./utils/wsTracker");
		if (window.requestIdleCallback) {
			window.requestIdleCallback(loadWs);
		} else {
			setTimeout(loadWs, 0);
		}
	}, []);

	useEffect(() => {
		if (import.meta.env.PROD) {
			if (window.requestIdleCallback) {
				window.requestIdleCallback(handlePwaRegistration);
			} else {
				setTimeout(handlePwaRegistration, 0);
			}
		}
	}, []);

	const appContent = (
		<ThemeProvider>
			<Suspense fallback={<LoadingSpinner size="lg" fullScreen />}> 
				<App />
			</Suspense>
		</ThemeProvider>
	);

	return import.meta.env.DEV ? <StrictMode>{appContent}</StrictMode> : appContent;
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");
createRoot(rootElement).render(<Main />);
