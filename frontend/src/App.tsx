import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { Toaster } from "@/components/ui/Sonner";
import { cleanupViewportHeight, initViewportHeight } from "@/utils/viewport";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import { AuthProvider } from "./store/auth/AuthProvider";
import {
	toasterConfig,
	getScreenSize,
} from "@/components/layouts/layoutConfig";

const queryClient = new QueryClient();

function App() {
	const [screenSize, setScreenSize] = useState(
		getScreenSize(window.innerWidth),
	);

	useEffect(() => {
		initViewportHeight();

		const handleResize = () => setScreenSize(getScreenSize(window.innerWidth));
		window.addEventListener("resize", handleResize);

		return () => {
			cleanupViewportHeight();
			window.removeEventListener("resize", handleResize);
		};
	}, []);

	return (
		<BrowserRouter>
			<QueryClientProvider client={queryClient}>
				<AuthProvider>
					<div
						className="flex flex-col h-[100dvh] min-h-[100svh]"
						style={{ height: "calc(var(--vh, 1vh) * 100)" }}
					>
						<Header />
						<main className="flex-1 overflow-y-auto">
							<div className="min-h-full flex flex-col items-center pt-20 pb-20 md:pt-24 md:pb-24">
								<div className="w-full md:max-w-screen-xl px-4 sm:px-6 lg:px-8 flex flex-col md:justify-center md:min-h-[calc(100dvh-10rem)] lg:min-h-[calc(100dvh-12rem)]">
									<AppRoutes />
								</div>
							</div>
						</main>
						<Footer />
					</div>
					<Toaster
						position={toasterConfig[screenSize].position}
						offset={toasterConfig[screenSize].offset}
						toastOptions={{ duration: 3000 }}
						style={{ width: toasterConfig[screenSize].width }}
					/>
				</AuthProvider>
				{import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
			</QueryClientProvider>
		</BrowserRouter>
	);
}

export default App;
