import { countries } from "countries-list";

export interface CountryOption {
	value: string;
	label: string;
}

export const getCountryOptions = (): CountryOption[] => {
	return Object.entries(countries)
		.map(([code, country]) => ({
			value: code,
			label: `${country.name} (${code})`,
		}))
		.sort((a, b) => a.label.localeCompare(b.label));
};
