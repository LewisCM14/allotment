import {
	getScreenSize,
	toasterConfig,
} from "@/components/layouts/layoutConfig";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Toaster as Sonner, type ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
	const { theme = "system" } = useTheme();
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
			style={
				{
					"--normal-bg": "var(--popover)",
					"--normal-text": "var(--popover-foreground)",
					"--normal-border": "var(--border)",
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
