import { defineConfig } from "vitest/config";
import path from "path";
import os from 'node:os';

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
        // UI-heavy tests (Radix Select interactions, React Query, etc.) can be slow under load
        // Bump global timeout to reduce flakiness in parallel runs
        testTimeout: 30000,

        // Enable parallel test execution with threads
        pool: 'threads',
        poolOptions: {
            threads: {
                minThreads: 2,
                maxThreads: Math.max(2, Math.floor(os.cpus().length * 0.75)),
            }
        },
        isolate: true, // Isolate each test file in its own thread

    // Additional performance settings: keep some parallelism but avoid oversubscription
    maxConcurrency: 5, // Maximum concurrent tests per worker
        sequence: {
            shuffle: true, // Randomize test order to identify interference issues
        },

        // Show slow tests in output for performance debugging
        slowTestThreshold: 2000, // Flag tests taking longer than 2 seconds

        // Generate HTML report
        reporters: ['default', 'html'],
        outputFile: {
            html: './coverage/html-report/index.html'
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
                "src/App.tsx",
                "coverage/**",
                "dist/**",
                "config/**", // All config files (vitest.setup.ts, vitest.config.ts, etc.)
                "src/components/ui/**", // Shadcn UI
                "src/types/**", // Type definitions
                "src/features/**/types/**",                 // Exclude all feature-level type definition folders
                "src/utils/**", // Utility wrappers
                "src/assets/**", // Static assets
                "src/store/**/AuthContext.tsx", // Auth context only
                "src/store/**/ThemeContext.tsx", // Theme context only
                "src/features/**/hooks/**", // Custom hooks
                "src/services/errorMonitoring.ts", // Infrastructure monitoring - non-critical
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
