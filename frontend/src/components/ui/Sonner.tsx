import {
	getScreenSize,
	toasterConfig,
} from "@/components/layouts/layoutConfig";
import { useTheme } from "@/store/theme/ThemeContext";
import { useEffect, useState } from "react";
import { Toaster as Sonner, type ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
	const { theme } = useTheme();
	const [screenSize, setScreenSize] = useState<"mobile" | "tablet" | "desktop">(
		"desktop",
	);

	useEffect(() => {
		const checkScreenSize = () => {
			setScreenSize(getScreenSize(window.innerWidth));
		};
		checkScreenSize();
		window.addEventListener("resize", checkScreenSize);
		return () => window.removeEventListener("resize", checkScreenSize);
	}, []);

	const config = toasterConfig[screenSize];

	return (
		<Sonner
			theme={theme as ToasterProps["theme"]}
			className="toaster group"
			position={config.position}
			closeButton
			toastOptions={{
				unstyled: true,
				classNames: {
					toast:
						"flex items-center gap-3 w-full rounded-lg border p-4 shadow-lg bg-card text-card-foreground border-border",
					title: "text-sm font-semibold text-foreground",
					description: "text-sm text-muted-foreground",
					actionButton:
						"bg-primary text-primary-foreground px-3 py-1.5 rounded-md text-sm font-medium",
					cancelButton:
						"bg-muted text-muted-foreground px-3 py-1.5 rounded-md text-sm font-medium",
					closeButton:
						"absolute right-2 top-2 rounded-md p-1 text-foreground/50 hover:text-foreground hover:bg-accent",
					success: "border-primary bg-primary/10",
					error: "border-destructive bg-destructive/10",
					info: "border-accent bg-accent/20",
					warning: "border-chart-4 bg-chart-4/20",
					icon: "text-foreground",
				},
			}}
			style={
				{
					"--z-index": "100",
					"--width": config.width,
					bottom: "calc(4rem + 20px)",
					display: "flex",
					flexDirection: "column-reverse",
					gap: "0.5rem",
				} as React.CSSProperties
			}
			{...props}
		/>
	);
};

export { Toaster };
