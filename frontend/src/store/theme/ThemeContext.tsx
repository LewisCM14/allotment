import { createContext, useContext } from "react";

export type Theme = "light" | "dark";

export interface IThemeContext {
	theme: Theme;
	toggleTheme: () => void;
}

export const ThemeContext = createContext<IThemeContext | undefined>(undefined);

export const useTheme = () => {
	const context = useContext(ThemeContext);
	if (context === undefined) {
		throw new Error("useTheme must be used within a ThemeProvider");
	}
	return context;
};
