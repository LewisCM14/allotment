import { useAuth } from "@/features/auth/AuthProvider";
import { useState } from "react";
import { HeaderView } from "./HeaderView";

interface NavLink {
	href: string;
	label: string;
}

const navLinks: NavLink[] = [
	{ href: "#", label: "Grow Guides" },
	{ href: "#", label: "Families" },
	{ href: "#", label: "Public Guides" },
];

export default function Header() {
	const [isOpen, setIsOpen] = useState(false);
	const { isAuthenticated } = useAuth();

	const handleMenuClick = () => {
		setIsOpen(!isOpen);
	};

	return (
		<HeaderView
			isOpen={isOpen}
			navLinks={isAuthenticated ? navLinks : []}
			onMenuClick={handleMenuClick}
			isAuthenticated={isAuthenticated}
		/>
	);
}
