import type React from "react";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "./Select";
import { cn } from "@/utils/utils";

interface Option {
	value: string;
	label: string;
}

interface FormSelectProps {
	id?: string;
	value: string | string[];
	onValueChange: (value: string | string[]) => void;
	placeholder: string;
	options: Option[];
	multiple?: boolean;
	error?: boolean;
	className?: string;
	disabled?: boolean;
	/** When true and a value is selected, renders an inline clear (reset) control */
	allowClear?: boolean;
}

export const FormSelect: React.FC<FormSelectProps> = ({
	id,
	value,
	onValueChange,
	placeholder,
	options,
	multiple = false,
	error = false,
	className,
	disabled = false,
	allowClear = false,
}) => {
	// For single select
	const handleSingleSelect = (val: string) => {
		onValueChange(val);
	};

	// For multi-select
	const handleMultiSelect = (val: string) => {
		if (Array.isArray(value)) {
			const newValue = value.includes(val)
				? value.filter((item) => item !== val)
				: [...value, val];
			onValueChange(newValue);
		} else {
			onValueChange([val]);
		}
	};

	// Determine if an option is selected
	const isSelected = (optionValue: string) => {
		if (multiple && Array.isArray(value)) {
			return value.includes(optionValue);
		}
		return value === optionValue;
	};

	// Format display value for trigger
	const displayValue = () => {
		if (multiple && Array.isArray(value) && value.length > 0) {
			const selectedLabels = options
				.filter((option) => value.includes(option.value))
				.map((option) => option.label);

			if (selectedLabels.length === 1) {
				return selectedLabels[0];
			}
			if (selectedLabels.length > 1) {
				return `${selectedLabels[0]} (+${selectedLabels.length - 1} more)`;
			}
		} else if (!multiple && typeof value === "string" && value) {
			const option = options.find((opt) => opt.value === value);
			return option ? option.label : placeholder;
		}

		return placeholder;
	};

	const radixValue = multiple
		? undefined // multi handled via custom click logic
		: (value as string);

	return (
		<div className={cn("relative w-full", className)}>
			<Select
				value={radixValue}
				onValueChange={multiple ? undefined : handleSingleSelect}
				disabled={disabled}
			>
				<SelectTrigger
					id={id}
					className={cn("w-full pr-8", error && "border-destructive")}
				>
					<SelectValue placeholder={placeholder} />
				</SelectTrigger>
				<SelectContent>
					{options.map((option) => (
						<SelectItem
							key={option.value}
							value={option.value}
							onClick={
								multiple ? () => handleMultiSelect(option.value) : undefined
							}
							className={
								multiple && isSelected(option.value)
									? "bg-accent text-accent-foreground"
									: ""
							}
						>
							{option.label}
						</SelectItem>
					))}
				</SelectContent>
			</Select>
			{allowClear && !disabled && (
				<button
					type="button"
					aria-label="Clear selection"
					onClick={(e) => {
						e.preventDefault();
						if (multiple) {
							onValueChange([]);
						} else {
							onValueChange("");
						}
					}}
					className={cn(
						"absolute inset-y-0 right-1 flex items-center rounded px-1 text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
						(!value || (Array.isArray(value) && value.length === 0)) &&
							"hidden",
					)}
				>
					&times;
				</button>
			)}
		</div>
	);
};
