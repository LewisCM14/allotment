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
import type { RegisterFormData } from "@/features/user/forms/RegisterSchema";
import { Check, ChevronsUpDown } from "lucide-react";
import {
	memo,
	useCallback,
	useEffect,
	useMemo,
	useRef,
	useState,
	useTransition,
} from "react";
import {
	type Control,
	Controller,
	type FieldError,
	type ControllerRenderProps,
} from "react-hook-form";
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
		const loadOptions = async () => {
			setIsLoading(true);
			const { getCountryOptions } = await import("@/utils/countries");
			const result = getCountryOptions();
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
	}, []);

	return { options, isLoading };
};

interface ICountrySelector {
	control: Control<RegisterFormData>;
	error?: FieldError;
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

const CountrySelector = memo(({ control, error }: ICountrySelector) => {
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

	const handleSelect = useCallback(
		(
			field: ControllerRenderProps<RegisterFormData, "country_code">,
			currentValue: string,
		) => {
			field.onChange(currentValue);
			setIsDropdownOpen(false);
			popoverStateRef.current.isOpen = false;
		},
		[],
	);

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
			return countryOptions.find((c) => c.value === fieldValue)?.label || "";
		},
		[countryOptions],
	);

	const rowRenderer = useCallback(
		(
			fieldValue: string,
			handleSelectFn: (
				field: ControllerRenderProps<RegisterFormData, "country_code">,
				value: string,
			) => void,
			field: ControllerRenderProps<RegisterFormData, "country_code">,
		) =>
			({ index, style }: { index: number; style: React.CSSProperties }) => {
				const country = filteredOptions[index];
				if (!country) return null;
				return (
					<CountryItemRenderer
						country={country}
						style={style}
						isSelected={fieldValue === country.value}
						onSelect={(value) => handleSelectFn(field, value)}
					/>
				);
			},
		[filteredOptions],
	);

	return (
		<>
			<Label htmlFor="country_code">Country</Label>
			<Controller
				control={control}
				name="country_code"
				render={({ field }) => {
					const selectedCountryLabel = getSelectedCountryLabel(field.value);
					const renderRow = rowRenderer(field.value, handleSelect, field);
					return (
						<Popover open={isDropdownOpen} onOpenChange={handleOpenChange}>
							<PopoverTrigger asChild>
								<Button
									variant="outline"
									aria-expanded={isDropdownOpen}
									className="w-full justify-between"
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
										{isLoading ? (
											<div className="py-6 text-center">Loading countries…</div>
										) : isPending ? (
											<div className="py-6 text-center">Searching…</div>
										) : filteredOptions.length === 0 ? (
											<CommandEmpty>No country found.</CommandEmpty>
										) : (
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
													{renderRow}
												</List>
											</CommandGroup>
										)}
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
});

CountrySelector.displayName = "CountrySelector";

export default CountrySelector;
