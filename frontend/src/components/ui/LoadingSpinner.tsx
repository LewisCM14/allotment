import { Loader2 } from "lucide-react";
import { cn } from "@/utils/utils";
import React from "react";

export interface LoadingSpinnerProps
	extends React.HTMLAttributes<HTMLOutputElement> {
	/** visual size */
	readonly size?: "sm" | "md" | "lg" | "xl";
	/** optional accessible label; defaults to "Loading" */
	readonly label?: string;
	/** center contents with flex */
	readonly center?: boolean;
	/** take full viewport (used for app shell) */
	readonly fullScreen?: boolean;
	/** delay (ms) before showing spinner to avoid flashes */
	readonly delay?: number;
	/** show inline (no default min height / centering) */
	readonly inline?: boolean;
}

const sizeMap: Record<NonNullable<LoadingSpinnerProps["size"]>, string> = {
	sm: "h-4 w-4",
	md: "h-6 w-6",
	lg: "h-8 w-8",
	xl: "h-12 w-12",
};

/**
 * Central loading spinner with optional delay + accessibility.
 * Use for page & major data fetch states. For inline button spinners you can still use this with size="sm" inline.
 */
export function LoadingSpinner({
	size = "md",
	label = "Loading",
	center = true,
	fullScreen = false,
	delay = 0,
	inline = false,
	className,
	...rest
}: LoadingSpinnerProps) {
	const [show, setShow] = React.useState(delay === 0);
	React.useEffect(() => {
		if (delay > 0) {
			const t = setTimeout(() => setShow(true), delay);
			return () => clearTimeout(t);
		}
	}, [delay]);

	if (!show) return null;

	const containerClasses = cn(
		!inline && center && "flex items-center justify-center",
		!inline &&
			fullScreen &&
			"fixed inset-0 z-50 bg-background/60 backdrop-blur-sm p-[env(safe-area-inset-top)] pr-[env(safe-area-inset-right)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)]",
		!inline && fullScreen && "min-h-[100dvh]",
		!inline && !fullScreen && center && "py-16",
		className,
	);

	return (
		<output
			/* Using semantic element instead of div+role=status to satisfy a11y lint rule */
			aria-live="polite"
			aria-label={label}
			className={cn("block", containerClasses)}
			{...rest}
		>
			<Loader2
				className={cn(sizeMap[size], "animate-spin text-primary")}
				aria-hidden="true"
			/>
			{label && !inline && <span className="sr-only">{label}</span>}
		</output>
	);
}

/** Helper component to wrap suspense fallbacks with consistent spinner */
export function SuspenseSpinnerFallback({
	size = "lg",
	delay = 120,
	fullScreen = false,
}: Readonly<{
	size?: LoadingSpinnerProps["size"];
	delay?: number;
	fullScreen?: boolean;
}>) {
	return <LoadingSpinner size={size} delay={delay} fullScreen={fullScreen} />;
}
