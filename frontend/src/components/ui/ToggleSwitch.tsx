import { cn } from "@/lib/utils";
import * as Switch from "@radix-ui/react-switch";
import { Moon, Sun } from "lucide-react";

interface IToggleSwitch {
	checked: boolean;
	onCheckedChange: (checked: boolean) => void;
	className?: string;
}

export function ToggleSwitch({
	checked,
	onCheckedChange,
	className,
}: IToggleSwitch) {
	return (
		<div className={cn("flex items-center gap-2", className)}>
			<Switch.Root
				checked={checked}
				onCheckedChange={onCheckedChange}
				className={cn(
					"peer inline-flex h-6 w-12 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors",
					"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
					"disabled:cursor-not-allowed disabled:opacity-50",
					"data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
				)}
			>
				<Switch.Thumb
					className={cn(
						"pointer-events-none flex items-center justify-center h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform",
						"data-[state=checked]:translate-x-6 data-[state=unchecked]:translate-x-0",
					)}
				>
					{checked ? (
						<Moon className="h-4 w-4 text-primary-foreground" />
					) : (
						<Sun className="h-4 w-4 text-primary-foreground" />
					)}
				</Switch.Thumb>
			</Switch.Root>
		</div>
	);
}
