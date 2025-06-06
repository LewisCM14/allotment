import path from "path";
import { defineConfig } from "vitest/config";

export default defineConfig({
    plugins: [],
    test: {
        environment: "jsdom",
        globals: true,
        setupFiles: [path.resolve(__dirname, "vitest.setup.ts")],
        alias: {
            "@": path.resolve(__dirname, "../src"),
        },
    },
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "../src"),
        },
    },
});
