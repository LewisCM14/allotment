import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { Toaster } from "@/components/ui/Sonner";
import { cleanupViewportHeight, initViewportHeight } from "@/utils/viewport";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import { AuthProvider } from "./store/auth/AuthProvider";

const queryClient = new QueryClient();

function App() {
	useEffect(() => {
		initViewportHeight();

		return () => {
			cleanupViewportHeight();
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
					<Toaster />
				</AuthProvider>
			</QueryClientProvider>
		</BrowserRouter>
	);
}

export default App;
