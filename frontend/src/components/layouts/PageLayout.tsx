import { widthClasses } from "@/components/layouts/layoutConfig";
import { cn } from "@/lib/utils";

interface IPageLayout extends React.HTMLAttributes<HTMLDivElement> {
	children: React.ReactNode;
	variant?: "default";
	centered?: boolean;
}

export function PageLayout({
	children,
	variant = "default",
	centered = true,
	className,
	...props
}: IPageLayout) {
	return (
		<main className="w-full">
			<div
				className={cn(
					"mx-auto",
					"px-4 py-6 md:px-6 md:py-8 lg:px-8",
					widthClasses[variant],
					className,
				)}
				{...props}
			>
				{children}
			</div>
		</main>
	);
}
