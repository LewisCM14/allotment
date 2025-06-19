import { Loader2 } from "lucide-react";
import { StrictMode, Suspense, lazy, useEffect } from "react";
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

	return (
		<StrictMode>
			<ThemeProvider>
				<Suspense
					fallback={
						<div className="flex h-screen w-screen items-center justify-center bg-background">
							<Loader2 className="h-8 w-8 animate-spin text-primary" />
						</div>
					}
				>
					<App />
				</Suspense>
			</ThemeProvider>
		</StrictMode>
	);
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");
createRoot(rootElement).render(<Main />);
