import { Button } from "@/components/ui/Button";
import { ToggleSwitch } from "@/components/ui/ToggleSwitch";
import { useTheme } from "@/context/ThemeContext";
import type { INavLink } from "@/types/NavigationTypes";
import { User } from "lucide-react";

interface IFooterPresenter {
	isOpen: boolean;
	navLinks: INavLink[];
	onMenuClick: () => void;
	closeMenu: () => void;
	isAuthenticated: boolean;
}

export function FooterPresenter({
	isOpen,
	navLinks,
	onMenuClick,
	closeMenu,
	isAuthenticated,
}: IFooterPresenter) {
	const currentYear = new Date().getFullYear();
	const contactEmail = import.meta.env.VITE_CONTACT_EMAIL;
	const { theme, toggleTheme } = useTheme();

	return (
		<>
			{isOpen && isAuthenticated && (
				<nav
					data-menu
					className="fixed bottom-16 left-0 w-full bg-card shadow-md p-4 flex flex-col space-y-2 z-50"
				>
					{navLinks.map((link) => (
						<a
							key={link.label}
							href={link.href}
							onClick={closeMenu}
							className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-all duration-200 hover:bg-accent/10 hover:translate-x-1"
						>
							{link.label}
						</a>
					))}
				</nav>
			)}

			<footer className="fixed bottom-0 left-0 w-full bg-card shadow-md z-50">
				<div className="max-w-7xl mx-auto p-4 flex items-center justify-between">
					<div className="w-1/3 flex items-center gap-4">
						{isAuthenticated && (
							<>
								<Button
									variant="ghost"
									onClick={onMenuClick}
									data-menu-button
									className="hover:bg-accent/10"
								>
									<User size={24} />
								</Button>
								<ToggleSwitch
									checked={theme === "dark"}
									onCheckedChange={() => toggleTheme()}
								/>
							</>
						)}
					</div>

					<div className="w-1/3 flex justify-center">
						<p className="text-card-foreground text-xs">© {currentYear}</p>
					</div>

					<div className="w-1/3 flex justify-end">
						<a
							href={`mailto:${contactEmail}`}
							className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-all duration-200 hover:bg-accent/10"
						>
							Contact
						</a>
					</div>
				</div>
			</footer>
		</>
	);
}
