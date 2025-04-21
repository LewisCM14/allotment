import { StrictMode, Suspense, lazy, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./global.css";

const App = lazy(() => import("./App.tsx"));

function Main() {
	useEffect(() => {
		let updateSW: () => void;
		import("virtual:pwa-register").then(({ registerSW }) => {
			updateSW = registerSW({
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
	}, []);

	return (
		<StrictMode>
			<Suspense fallback={null}>
				<App />
			</Suspense>
		</StrictMode>
	);
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");
createRoot(rootElement).render(<Main />);
