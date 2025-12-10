import { Button } from "@/components/ui/Button";
import {
	Command,
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
} from "@/components/ui/Command";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/Popover";
import { getCountryOptions } from "@/utils/countries";
import { Check, ChevronsUpDown } from "lucide-react";
import {
	memo,
	useCallback,
	useEffect,
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
import type { UserProfileFormData } from "../forms/UserProfileSchema";

const useCountryOptions = () => {
	const [options, setOptions] = useState<
		Array<{ value: string; label: string; lowerLabel: string }>
	>([]);
	const [isLoading, setIsLoading] = useState(true);

	useEffect(() => {
		const loadOptions = async () => {
			try {
				const countries = await getCountryOptions();
				const formattedOptions = countries.map((country) => ({
					value: country.value,
					label: country.label,
					lowerLabel: country.label.toLowerCase(),
				}));
				setOptions(formattedOptions);
			} catch (error) {
				console.error("Failed to load country options:", error);
				setOptions([]);
			} finally {
				setIsLoading(false);
			}
		};

		loadOptions();
	}, []);

	return { options, isLoading };
};

interface UserProfileCountrySelectorProps {
	control: Control<UserProfileFormData>;
	error?: FieldError;
}

const ITEM_HEIGHT = 36;
const LIST_HEIGHT = 250;

const UserProfileCountrySelector = memo(
	({ control, error }: UserProfileCountrySelectorProps) => {
		const [isDropdownOpen, setIsDropdownOpen] = useState(false);
		const [searchValue, setSearchValue] = useState("");
		const [filteredOptions, setFilteredOptions] = useState<
			Array<{ value: string; label: string; lowerLabel: string }>
		>([]);
		const [isPending, startTransition] = useTransition();
		const inputRef = useRef<HTMLInputElement>(null);

		const { options: countryOptions, isLoading } = useCountryOptions();

		// Store the dropdown state in a ref to avoid re-renders
		const popoverStateRef = useRef({ isOpen: false });

		// Filter options based on search
		useEffect(() => {
			if (isDropdownOpen && !isLoading) {
				const lower = searchValue.toLowerCase();
				startTransition(() => {
					setFilteredOptions(
						countryOptions.filter((opt) => opt.lowerLabel.includes(lower)),
					);
				});
			}
		}, [searchValue, countryOptions, isLoading, isDropdownOpen]);

		// Reset when opening
		useEffect(() => {
			if (isDropdownOpen && !isLoading) {
				startTransition(() => {
					setFilteredOptions(countryOptions);
				});
			}
		}, [isDropdownOpen, countryOptions, isLoading]);

		const handleSelect = useCallback(
			(
				field: ControllerRenderProps<UserProfileFormData, "user_country_code">,
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

		return (
			<Controller
				control={control}
				name="user_country_code"
				render={({ field }) => {
					const selectedCountry = countryOptions.find(
						(country) => country.value === field.value,
					);

					return (
						<div className="space-y-2">
							<Popover open={isDropdownOpen} onOpenChange={handleOpenChange}>
								<PopoverTrigger asChild>
									<Button
										variant="outline"
										aria-haspopup="listbox"
										aria-expanded={isDropdownOpen}
										aria-label="Select country"
										className="w-full justify-between"
									>
										{selectedCountry
											? selectedCountry.label
											: "Select country..."}
										<ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
									</Button>
								</PopoverTrigger>
								<PopoverContent className="w-full p-0" align="start">
									<Command shouldFilter={false}>
										<CommandInput
											ref={inputRef}
											placeholder="Search countries..."
											value={searchValue}
											onValueChange={setSearchValue}
										/>
										<CommandEmpty>No countries found.</CommandEmpty>
										<CommandGroup>
											<div
												style={{
													height: Math.min(
														LIST_HEIGHT,
														filteredOptions.length * ITEM_HEIGHT,
													),
												}}
											>
												{!isPending &&
													filteredOptions.slice(0, 50).map((country) => (
														<CommandItem
															key={country.value}
															value={country.value}
															onSelect={() =>
																handleSelect(field, country.value)
															}
															className="px-2 py-1"
														>
															<Check
																className={`mr-2 h-4 w-4 ${
																	field.value === country.value
																		? "opacity-100"
																		: "opacity-0"
																}`}
															/>
															{country.label}
														</CommandItem>
													))}
											</div>
										</CommandGroup>
									</Command>
								</PopoverContent>
							</Popover>
							{error && (
								<p className="text-sm text-destructive">{error.message}</p>
							)}
						</div>
					);
				}}
			/>
		);
	},
);

UserProfileCountrySelector.displayName = "UserProfileCountrySelector";

export default UserProfileCountrySelector;
