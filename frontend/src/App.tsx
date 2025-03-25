import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./features/auth/AuthProvider";
import AppRoutes from "./routes/AppRoutes";

function App() {
	return (
		<AuthProvider>
			<ThemeProvider>
				<div className="h-screen flex flex-col">
					<Header />
					<div className="flex-1 mb-16">
						<AppRoutes />
					</div>
					<Footer />
				</div>
			</ThemeProvider>
		</AuthProvider>
	);
}

export default App;
