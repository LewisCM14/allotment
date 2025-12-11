import { Button } from "@/components/ui/Button";
import {
	Command,
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
} from "@/components/ui/Command";
import { Label } from "@/components/ui/Label";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/Popover";
import { Check, ChevronsUpDown } from "lucide-react";
import {
	memo,
	useCallback,
	useEffect,
	useRef,
	useState,
	useTransition,
} from "react";
import type React from "react";
import { type Control, Controller, type FieldError } from "react-hook-form";
import { FixedSizeList as List } from "react-window";

function useDebounce<T>(value: T, delay: number): T {
	const [debouncedValue, setDebouncedValue] = useState<T>(value);

	useEffect(() => {
		const timer = setTimeout(() => {
			setDebouncedValue(value);
		}, delay);

		return () => {
			clearTimeout(timer);
		};
	}, [value, delay]);

	return debouncedValue;
}

const useCountryOptions = () => {
	const [options, setOptions] = useState<
		Array<{ value: string; label: string; lowerLabel: string }>
	>([]);
	const [isLoading, setIsLoading] = useState(true);

	useEffect(() => {
		let isMounted = true;
		const loadOptions = async () => {
			setIsLoading(true);
			const { getCountryOptions } = await import("@/utils/countries");
			if (!isMounted) return;
			const result = await getCountryOptions();
			setOptions(
				result.map((c) => ({
					value: c.value,
					label: c.label,
					lowerLabel: c.label.toLowerCase(),
				})),
			);
			setIsLoading(false);
		};

		loadOptions();
		return () => {
			isMounted = false;
		};
	}, []);

	return { options, isLoading };
};

interface ICountrySelector {
	// biome-ignore lint/suspicious/noExplicitAny: Required for lazy-loaded generic component compatibility
	readonly control: Control<any>;
	readonly name: string;
	readonly error?: FieldError;
	readonly label?: string;
	readonly showLabel?: boolean;
}

const ITEM_HEIGHT = 36;
const LIST_HEIGHT = 250;
const OVERSCAN_COUNT = 10;

const CountryItemRenderer = memo(
	({
		country,
		style,
		isSelected,
		onSelect,
	}: {
		country: { value: string; label: string };
		style: React.CSSProperties;
		isSelected: boolean;
		onSelect: (value: string) => void;
	}) => (
		<CommandItem
			key={country.value}
			value={country.value}
			onSelect={() => onSelect(country.value)}
			style={style}
			className="px-2 py-1"
		>
			<Check
				className={`mr-2 h-4 w-4 ${isSelected ? "opacity-100" : "opacity-0"}`}
			/>
			{country.label}
		</CommandItem>
	),
);

CountryItemRenderer.displayName = "CountryItemRenderer";

interface CountryListRowRendererProps {
	filteredOptions: Array<{ value: string; label: string }>;
	fieldValue: string;
	onSelectValue: (value: string) => void;
	index: number;
	style: React.CSSProperties;
}

const CountryListRowRenderer = memo(
	({
		filteredOptions,
		fieldValue,
		onSelectValue,
		index,
		style,
	}: CountryListRowRendererProps) => {
		const country = filteredOptions[index];
		if (!country) return null;
		return (
			<CountryItemRenderer
				country={country}
				style={style}
				isSelected={fieldValue === country.value}
				onSelect={onSelectValue}
			/>
		);
	},
);
CountryListRowRenderer.displayName = "CountryListRowRenderer";

function CountrySelectorInner({
	control,
	name,
	error,
	label = "Country",
	showLabel = true,
}: ICountrySelector) {
	const [isDropdownOpen, setIsDropdownOpen] = useState(false);
	const { options: countryOptions, isLoading } = useCountryOptions();

	const [searchValue, setSearchValue] = useState("");
	const debouncedSearchValue = useDebounce(searchValue, 200);
	const [filteredOptions, setFilteredOptions] = useState<
		Array<{ value: string; label: string }>
	>([]);
	const inputRef = useRef<HTMLInputElement>(null);
	const [isPending, startTransition] = useTransition();

	// Store the dropdown state in a ref to avoid re-renders
	const popoverStateRef = useRef({ isOpen: false });

	// Prevent body scroll when dropdown is open (fixes mobile scroll issue)
	useEffect(() => {
		if (isDropdownOpen) {
			// Store original overflow value
			const originalOverflow = document.body.style.overflow;
			const originalPosition = document.body.style.position;

			// Prevent scrolling
			document.body.style.overflow = "hidden";
			document.body.style.position = "relative";

			// Cleanup function to restore original styles
			return () => {
				document.body.style.overflow = originalOverflow;
				document.body.style.position = originalPosition;
			};
		}
	}, [isDropdownOpen]);

	// filtered on debounced search
	useEffect(() => {
		if (isDropdownOpen && !isLoading) {
			const lower = debouncedSearchValue.toLowerCase();
			startTransition(() => {
				setFilteredOptions(
					countryOptions.filter((opt) => opt.lowerLabel.includes(lower)),
				);
			});
		}
	}, [debouncedSearchValue, countryOptions, isLoading, isDropdownOpen]);

	// reset when opening
	useEffect(() => {
		if (isDropdownOpen && !isLoading) {
			startTransition(() => {
				setFilteredOptions(countryOptions);
			});
		}
	}, [isDropdownOpen, countryOptions, isLoading]);

	const handleOpenChange = useCallback(
		(isOpen: boolean) => {
			popoverStateRef.current.isOpen = isOpen;
			if (isDropdownOpen !== isOpen) {
				setIsDropdownOpen(isOpen);
			}
			if (isOpen) {
				setSearchValue("");
				requestAnimationFrame(() => {
					inputRef.current?.focus();
				});
			}
		},
		[isDropdownOpen],
	);

	const getSelectedCountryLabel = useCallback(
		(fieldValue: string) => {
			if (!fieldValue) return "";
			return countryOptions.find((c) => c.value === fieldValue)?.label ?? "";
		},
		[countryOptions],
	);

	return (
		<>
			{showLabel && <Label htmlFor={name}>{label}</Label>}
			<Controller
				control={control}
				name={name}
				render={({ field }) => {
					const selectedCountryLabel = getSelectedCountryLabel(
						field.value as string,
					);

					const handleSelectValue = (value: string) => {
						field.onChange(value);
						setIsDropdownOpen(false);
						popoverStateRef.current.isOpen = false;
					};

					const renderCommandContent = () => {
						if (isLoading) {
							return <div className="py-6 text-center">Loading countries…</div>;
						}

						if (isPending) {
							return <div className="py-6 text-center">Searching…</div>;
						}

						if (filteredOptions.length === 0) {
							return <CommandEmpty>No country found.</CommandEmpty>;
						}

						return (
							<CommandGroup className="overflow-hidden p-0">
								<List
									height={Math.min(
										LIST_HEIGHT,
										filteredOptions.length * ITEM_HEIGHT,
									)}
									width="100%"
									itemCount={filteredOptions.length}
									itemSize={ITEM_HEIGHT}
									overscanCount={OVERSCAN_COUNT}
									className="scrollbar-thin"
								>
									{({ index, style }) => (
										<CountryListRowRenderer
											filteredOptions={filteredOptions}
											fieldValue={field.value as string}
											onSelectValue={handleSelectValue}
											index={index}
											style={style}
										/>
									)}
								</List>
							</CommandGroup>
						);
					};

					return (
						<Popover open={isDropdownOpen} onOpenChange={handleOpenChange}>
							<PopoverTrigger asChild>
								<Button
									variant="outline"
									aria-expanded={isDropdownOpen}
									aria-label="Select country"
									className="w-full justify-between bg-card border-border text-foreground hover:bg-accent hover:text-foreground dark:bg-card dark:border-border"
								>
									{selectedCountryLabel || "Select country..."}
									<ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
								</Button>
							</PopoverTrigger>
							{isDropdownOpen && (
								<PopoverContent
									className="w-full p-0"
									onEscapeKeyDown={() => setIsDropdownOpen(false)}
								>
									<Command className="max-h-[350px]">
										<CommandInput
											placeholder="Search country..."
											value={searchValue}
											onValueChange={setSearchValue}
											ref={inputRef}
											className="border-none focus:ring-0"
										/>
										{renderCommandContent()}
									</Command>
								</PopoverContent>
							)}
						</Popover>
					);
				}}
			/>
			{error && <p className="text-sm text-red-500">{error.message}</p>}
		</>
	);
}

// Export the inner function directly to preserve generics
// memo is applied to child components (CountryItemRenderer, CountryListRowRenderer)
// which provides the performance benefit where it matters most
export default CountrySelectorInner;
