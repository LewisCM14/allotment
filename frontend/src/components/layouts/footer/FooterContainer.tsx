import { useLogout } from "@/hooks/useLogout";
import { useAuth } from "@/store/auth/AuthContext";
import type { INavLink } from "@/types/NavigationTypes";
import { useCallback, useEffect, useState } from "react";
import { FooterPresenter } from "./FooterPresenter";

export default function Footer() {
	const [isOpen, setIsOpen] = useState(false);
	const { isAuthenticated } = useAuth();
	const logout = useLogout();

	const navLinks: INavLink[] = [
		{ href: "#", label: "Profile" },
		{ href: "#", label: "Allotment" },
		{ href: "#", label: "Preferences" },
		// { href: "#", label: "Notifications" },
		{
			href: "#",
			label: "Sign Out",
			onClick: (e) => {
				e.preventDefault();
				logout();
				closeMenu();
			},
		},
	];

	const handleMenuClick = useCallback(() => {
		setIsOpen((prev) => !prev);
	}, []);

	const closeMenu = useCallback(() => {
		setIsOpen(false);
	}, []);

	const handleClickOutside = useCallback(
		(event: MouseEvent) => {
			const menuElement = document.querySelector("[data-menu]");
			const buttonElement = document.querySelector("[data-menu-button]");

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
		<FooterPresenter
			isOpen={isOpen}
			navLinks={isAuthenticated ? navLinks : []}
			onMenuClick={handleMenuClick}
			isAuthenticated={isAuthenticated}
			closeMenu={closeMenu}
		/>
	);
}
