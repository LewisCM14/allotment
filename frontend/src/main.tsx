import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./global.css";

function Main() {
	useEffect(() => {
		// @ts-ignore: no types for wsTracker
		import("./utils/wsTracker.js");
	}, []);

	useEffect(() => {
		if (import.meta.env.PROD) {
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
		}
	}, []);

	return (
		<StrictMode>
			<App />
		</StrictMode>
	);
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Failed to find the root element");
createRoot(rootElement).render(<Main />);
