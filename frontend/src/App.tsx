import Footer from "@/components/layouts/footer/FooterContainer";
import Header from "@/components/layouts/header/HeaderContainer";
import { AuthProvider } from "./features/auth/AuthProvider";
import AppRoutes from "./routes/AppRoutes";

function App() {
	return (
		<AuthProvider>
			<div className="h-screen flex flex-col">
				<Header />
				<div className="flex-1 mb-16">
					<AppRoutes />
				</div>
				<Footer />
			</div>
		</AuthProvider>
	);
}

export default App;
