import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { toast } from "sonner";
import { registerSW } from "virtual:pwa-register";
import App from "./App.tsx";
import "./global.css";

const updateSW = registerSW({
	onNeedRefresh() {
		if (confirm("New content available. Reload?")) {
			updateSW();
		}
	},
	onOfflineReady() {
		toast.success("App ready to work offline", {
			description: "You can use the app even without an internet connection",
			duration: 3000,
		});
	},
});

const rootElement = document.getElementById("root");

if (!rootElement) {
	throw new Error("Failed to find the root element");
}

const root = createRoot(rootElement);

root.render(
	<StrictMode>
		<App />
	</StrictMode>,
);
