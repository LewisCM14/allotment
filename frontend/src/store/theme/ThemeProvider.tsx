import { useCallback, useEffect, useMemo, useState } from "react";
import { type Theme, ThemeContext } from "./ThemeContext";

interface IThemeProvider {
	children: React.ReactNode;
}

export function ThemeProvider({ children }: IThemeProvider) {
	const [theme, setTheme] = useState<Theme>(() => {
		const stored = localStorage.getItem("theme");
		if (stored === "light" || stored === "dark") return stored;
		return window.matchMedia("(prefers-color-scheme: dark)").matches
			? "dark"
			: "light";
	});

	useEffect(() => {
		const root = window.document.documentElement;
		root.classList.remove("light", "dark");
		root.classList.add(theme);
		localStorage.setItem("theme", theme);
	}, [theme]);

	const toggleTheme = useCallback(() => {
		setTheme((prev) => (prev === "light" ? "dark" : "light"));
	}, []);

	const themeContextValue = useMemo(
		() => ({ theme, toggleTheme }),
		[theme, toggleTheme],
	);

	return (
		<ThemeContext.Provider value={themeContextValue}>
			{children}
		</ThemeContext.Provider>
	);
}
