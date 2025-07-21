import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
    resolve: {
        alias: {
            "@": path.resolve(process.cwd(), "src"),
        },
    },
    test: {
        environment: "jsdom",
        globals: true,
        setupFiles: [path.resolve(__dirname, "vitest.setup.ts")],
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
                "src/App.tsx",
                "coverage/**",
                "dist/**",
                "src/components/ui/**", // Shadcn UI
                "src/types/**", // Type definitions
                "src/utils/**", // Utility wrappers
                "src/assets/**", // Static assets
                "src/store/**/AuthContext.tsx", // Auth context only
                "src/store/**/ThemeContext.tsx", // Theme context only
                "src/features/**/hooks/**", // Custom hooks (optional, review)
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
});
