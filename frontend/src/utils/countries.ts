export interface ICountryOption {
	value: string;
	label: string;
}

// Lazy load countries data to reduce initial bundle size
export const getCountryOptions = async (): Promise<ICountryOption[]> => {
	const { countries } = await import("countries-list");
	return Object.entries(countries)
		.map(([code, country]) => ({
			value: code,
			label: `${country.name} (${code})`,
		}))
		.sort((a, b) => a.label.localeCompare(b.label));
};
