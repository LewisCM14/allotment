import { cn } from "@/lib/utils";

interface PageLayoutProps extends React.HTMLAttributes<HTMLDivElement> {
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
}: PageLayoutProps) {
	const widthClasses = {
		default: "w-[96%] md:w-[84%] lg:w-[66%]",
	};

	return (
		<main className="h-full w-full flex items-center justify-center">
			<div
				className={cn(
					"mx-auto",
					"px-4 py-6 md:px-6 md:py-8 lg:px-8",
					centered && "flex items-center justify-center",
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
