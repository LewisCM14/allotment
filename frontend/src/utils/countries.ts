import { countries } from "countries-list";

export interface ICountryOption {
	value: string;
	label: string;
}

export const getCountryOptions = (): ICountryOption[] => {
	return Object.entries(countries)
		.map(([code, country]) => ({
			value: code,
			label: `${country.name} (${code})`,
		}))
		.sort((a, b) => a.label.localeCompare(b.label));
};
