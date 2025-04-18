import { Button } from "@/components/ui/Button";
import type { INavLink } from "@/types/NavigationTypes";
import { Menu } from "lucide-react";

interface IHeaderPresenter {
	isOpen: boolean;
	navLinks: INavLink[];
	onMenuClick: () => void;
	closeMenu: () => void;
	isAuthenticated: boolean;
}

export function HeaderPresenter({
	isOpen,
	navLinks,
	onMenuClick,
	closeMenu,
	isAuthenticated,
}: IHeaderPresenter) {
	const appTitle = import.meta.env.VITE_APP_TITLE || "Allotment";

	return (
		<header className="fixed top-0 left-0 w-full bg-card shadow-md z-50">
			<div className="mx-auto flex justify-between items-center p-4">
				<h1 className="text-xl font-bold text-card-foreground">
					<a href="/" className="hover:underline">
						{appTitle}
					</a>
				</h1>

				{/* Desktop Navigation */}
				<nav className="hidden md:flex space-x-4">
					{isAuthenticated ? (
						navLinks.map((link) => (
							<a
								key={link.label}
								href={link.href}
								className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-all duration-200 hover:bg-accent/10"
							>
								{link.label}
							</a>
						))
					) : (
						<a
							href="/login"
							className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-all duration-200 hover:bg-accent/10"
						>
							Login
						</a>
					)}
				</nav>

				{/* Mobile Menu Button */}
				{isAuthenticated && (
					<Button
						variant="ghost"
						className="md:hidden"
						onClick={onMenuClick}
						data-header-button
					>
						<Menu size={24} />
					</Button>
				)}
			</div>

			{/* Mobile Menu */}
			{isOpen && isAuthenticated && (
				<nav
					data-header-menu
					className="md:hidden bg-card shadow-md p-4 flex flex-col space-y-2"
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
		</header>
	);
}
