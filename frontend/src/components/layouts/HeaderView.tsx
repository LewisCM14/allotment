import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

interface NavLink {
	href: string;
	label: string;
}

interface HeaderViewProps {
	isOpen: boolean;
	navLinks: NavLink[];
	onMenuClick: () => void;
	isAuthenticated: boolean;
}

export function HeaderView({
	isOpen,
	navLinks,
	onMenuClick,
	isAuthenticated,
}: HeaderViewProps) {
	return (
		<header className="fixed top-0 left-0 w-full bg-card shadow-md z-50">
			<div className="max-w-7xl mx-auto flex justify-between items-center p-4">
				<h1 className="text-xl font-bold text-card-foreground">Allotment</h1>

				{/* Desktop Navigation */}
				<nav className="hidden md:flex space-x-4">
					{isAuthenticated ? (
						navLinks.map((link) => (
							<a
								key={link.label}
								href={link.href}
								className="text-muted-foreground hover:text-card-foreground"
							>
								{link.label}
							</a>
						))
					) : (
						<a
							href="/login"
							className="text-muted-foreground hover:text-card-foreground"
						>
							Login
						</a>
					)}
				</nav>

				{isAuthenticated && (
					<Button variant="ghost" className="md:hidden" onClick={onMenuClick}>
						<Menu size={24} />
					</Button>
				)}
			</div>

			{/* Mobile Menu */}
			{isOpen && isAuthenticated && (
				<nav className="md:hidden bg-card shadow-md p-4 flex flex-col space-y-2">
					{navLinks.map((link) => (
						<a
							key={link.label}
							href={link.href}
							className="text-muted-foreground hover:text-card-foreground"
						>
							{link.label}
						</a>
					))}
				</nav>
			)}
		</header>
	);
}
