import { Input } from "./Input";
import { Search } from "lucide-react";
import { cn } from "@/utils/utils";
import type { InputHTMLAttributes } from "react";

interface SearchFieldProps {
	readonly value: string;
	readonly onChange: (value: string) => void;
	readonly placeholder?: string;
	readonly ariaLabel?: string;
	readonly className?: string;
	readonly inputProps?: Omit<
		InputHTMLAttributes<HTMLInputElement>,
		"value" | "onChange" | "placeholder" | "aria-label"
	>;
}

export function SearchField({
	value,
	onChange,
	placeholder = "Search...",
	ariaLabel = "Search",
	className,
	inputProps,
}: SearchFieldProps) {
	return (
		<div className={cn("relative", className)}>
			<Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
			<Input
				placeholder={placeholder}
				className="pl-10"
				value={value}
				onChange={(e) => onChange(e.target.value)}
				aria-label={ariaLabel}
				{...inputProps}
			/>
		</div>
	);
}
