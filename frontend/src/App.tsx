import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { Toaster } from "@/components/ui/Sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import { AuthProvider } from "./store/auth/AuthProvider";
import { ThemeProvider } from "./store/theme/ThemeProvider";

const queryClient = new QueryClient();

function App() {
	return (
		<BrowserRouter>
			<QueryClientProvider client={queryClient}>
				<AuthProvider>
					<ThemeProvider>
						<div className="flex flex-col h-screen">
							<Header />
							<div className="flex-1 overflow-y-auto pt-16 md:pt-24 pb-16">
								<AppRoutes />
							</div>
							<Footer />
						</div>
						<Toaster />
					</ThemeProvider>
				</AuthProvider>
			</QueryClientProvider>
		</BrowserRouter>
	);
}

export default App;
