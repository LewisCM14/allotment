import { useAuth } from "@/store/auth/AuthContext";
import type { INavLink } from "@/types/NavigationTypes";
import { useCallback, useEffect, useState } from "react";
import { HeaderPresenter } from "./HeaderPresenter";

const navLinks: INavLink[] = [
	{ href: "#", label: "Grow Guides" },
	{ href: "#", label: "Families" },
	{ href: "#", label: "Public Guides" },
];

export default function Header() {
	const [isOpen, setIsOpen] = useState(false);
	const { isAuthenticated } = useAuth();

	const handleMenuClick = useCallback(() => {
		setIsOpen((prev) => !prev);
	}, []);

	const closeMenu = useCallback(() => {
		setIsOpen(false);
	}, []);

	const handleClickOutside = useCallback(
		(event: MouseEvent) => {
			const menuElement = document.querySelector("[data-header-menu]");
			const buttonElement = document.querySelector("[data-header-button]");

			if (
				menuElement &&
				!menuElement.contains(event.target as Node) &&
				!buttonElement?.contains(event.target as Node) &&
				isOpen
			) {
				closeMenu();
			}
		},
		[isOpen, closeMenu],
	);

	useEffect(() => {
		document.addEventListener("mousedown", handleClickOutside);
		return () => document.removeEventListener("mousedown", handleClickOutside);
	}, [handleClickOutside]);

	return (
		<HeaderPresenter
			isOpen={isOpen}
			navLinks={isAuthenticated ? navLinks : []}
			onMenuClick={handleMenuClick}
			closeMenu={closeMenu}
			isAuthenticated={isAuthenticated}
		/>
	);
}
