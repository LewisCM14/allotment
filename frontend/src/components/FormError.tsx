import { cn } from "@/utils/utils";
import { AlertCircle } from "lucide-react";

interface IFormError {
	readonly message?: string;
	readonly className?: string;
}

export function FormError({ message, className }: IFormError) {
	if (!message) return null;

	return (
		<div
			className={cn("flex items-center gap-2 text-sm text-red-500", className)}
		>
			<AlertCircle className="h-4 w-4" />
			<span>{message}</span>
		</div>
	);
}
