// Dynamically import all *Handlers.ts files in this directory and combine their handler arrays
// This works with Vite's import.meta.glob
const handlerModules = import.meta.glob("./*Handlers.ts", { eager: true });

export const handlers = Object.values(handlerModules).flatMap((mod) =>
	Object.values(mod as Record<string, unknown>)
		.filter(Array.isArray)
		.flat(),
);
