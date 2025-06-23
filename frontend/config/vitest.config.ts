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
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "html", "lcov"],
            reportsDirectory: "./coverage",
            exclude: [
                "node_modules/**",
                "src/setupTests.ts",
                "src/mocks/**",
                "src/**/*.d.ts",
                "src/vite-env.d.ts",
                "**/*.config.ts",
                "**/*.config.js",
                "src/main.tsx",
                "src/ServiceWorker.ts",
                "coverage/**",
                "dist/**"
            ],
            include: [
                "src/**/*.{ts,tsx}"
            ],
            all: true,
            thresholds: {
                global: {
                    branches: 80,
                    functions: 80,
                    lines: 80,
                    statements: 80
                }
            }
        }
    },
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "../src"),
        },
    },
});
