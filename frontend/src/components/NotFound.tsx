import { Button } from "@/components/ui/Button";
import { useNavigate } from "react-router-dom";

const NotFound = () => {
	const navigate = useNavigate();

	return (
		<div className="flex flex-col items-center justify-center h-full p-6 text-center">
			<h1 className="text-4xl font-bold mb-4">404</h1>
			<h2 className="text-2xl font-semibold mb-4">Page Not Found</h2>
			<p className="text-muted-foreground mb-6">
				The page you are looking for doesn't exist or has been moved.
			</p>
			<div className="flex gap-4">
				<Button onClick={() => navigate(-1)} variant="outline">
					Go Back
				</Button>
				<Button
					onClick={() => navigate("/")}
					variant="default"
					className="text-white"
				>
					Go Home
				</Button>
			</div>
		</div>
	);
};

export default NotFound;
