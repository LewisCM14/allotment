import logo32 from "@/assets/logo_32x32.webp";
import logo64 from "@/assets/logo_64x64.webp";
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
	const appTitle =
		window.envConfig?.VITE_APP_TITLE ||
		import.meta.env.VITE_APP_TITLE ||
		"Allotment";

	return (
		<header className="fixed top-0 left-0 w-full bg-card shadow-md z-50">
			<div className="mx-auto flex justify-between items-center p-4">
				<h1 className="text-xl font-bold text-card-foreground flex items-center space-x-2">
					<img
						fetchPriority="high"
						loading="eager"
						src={logo32}
						srcSet={`${logo32} 32w, ${logo64} 64w`}
						sizes="(min-width: 768px) 64px, 32px"
						width={32}
						height={32}
						alt="Logo"
						className="h-8 w-8 md:h-16 md:w-16"
					/>
					<a
						href="/"
						className="underline decoration-transparent decoration-1 hover:decoration-current transition-colors"
					>
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
								className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-transform duration-200 hover:translate-x-1"
							>
								{link.label}
							</a>
						))
					) : (
						<a
							href="/login"
							className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-transform duration-200 hover:translate-x-1"
						>
							Login
						</a>
					)}
				</nav>

				{/* Mobile Menu Button */}
				{isAuthenticated && (
					<Button
						variant="ghost"
						aria-label="Toggle navigation menu"
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
							className="text-muted-foreground hover:text-card-foreground p-2 rounded-md transition-transform duration-200 hover:translate-x-1"
						>
							{link.label}
						</a>
					))}
				</nav>
			)}
		</header>
	);
}
