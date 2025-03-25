import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { AuthProvider } from "./features/user/AuthProvider";
import AppRoutes from "./routes/AppRoutes";
import { ThemeProvider } from "./store/theme/ThemeContext";

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
