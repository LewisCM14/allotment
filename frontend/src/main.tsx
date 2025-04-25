import { StrictMode, Suspense, lazy, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./global.css";

const App = lazy(() => import("./App.tsx"));

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
			const registerPWA = () =>
				import("virtual:pwa-register").then(({ registerSW }) => {
					const updateSW = registerSW({
						onNeedRefresh() {
							if (confirm("New content available. Reload?")) {
								updateSW();
							}
						},
						onOfflineReady() {
							import("sonner").then(({ toast }) =>
								toast.success("App ready to work offline", {
									description:
										"You can use the app even without an internet connection",
									duration: 3000,
								}),
							);
						},
					});
				});
			if (window.requestIdleCallback) {
				window.requestIdleCallback(registerPWA);
			} else {
				setTimeout(registerPWA, 0);
			}
		}
	}, []);

	return (
		<StrictMode>
			<Suspense fallback={<div>Loading...</div>}>
				<App />
			</Suspense>
		</StrictMode>
	);
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");
createRoot(rootElement).render(<Main />);
