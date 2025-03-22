import { BrowserRouter, Route, Routes } from "react-router-dom";
import LoginForm from "../features/auth/LoginForm";
// import NotFound from "../components/NotFound";
// import ProtectedRoute from "./ProtectedRoute";

const AppRoutes = () => {
	return (
		<BrowserRouter>
			<Routes>
				{/* Public routes */}
				<Route path="/login" element={<LoginForm />} />

				{/* Protected routes */}
				{/* <Route element={}>
                    <Route path="/" element={
                        <ProtectedRoute>
                        </ProtectedRoute>
                    } />
                </Route> */}

				{/* Handle undefined routes */}
				{/* <Route path="*" element={<NotFound />} /> */}
			</Routes>
		</BrowserRouter>
	);
};

export default AppRoutes;
