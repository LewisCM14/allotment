import { Input } from "./Input";
import { Search } from "lucide-react";
import { cn } from "@/utils/utils";
import type { InputHTMLAttributes } from "react";

interface SearchFieldProps {
	value: string;
	onChange: (value: string) => void;
	placeholder?: string;
	ariaLabel?: string;
	className?: string;
	inputProps?: Omit<
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
