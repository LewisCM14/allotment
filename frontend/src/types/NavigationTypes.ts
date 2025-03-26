export interface INavLink {
	href: string;
	label: string;
	onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
}
