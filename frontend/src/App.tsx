import Header from "@/components/layouts/Header";
import { AuthProvider } from "./features/auth/AuthProvider";
import AppRoutes from "./routes/AppRoutes";

function App() {
	return (
		<AuthProvider>
			<div className="h-screen flex flex-col">
				<Header />
				<div className="flex-1">
					<AppRoutes />
				</div>
			</div>
		</AuthProvider>
	);
}

export default App;
