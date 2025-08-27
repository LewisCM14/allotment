import tailwindcss from '@tailwindcss/vite';
import legacy from "@vitejs/plugin-legacy";
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { defineConfig } from 'vite';
import { imagetools } from 'vite-imagetools';
import compression from 'vite-plugin-compression';
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig(() => {
    return {
        base: './', // Ensures assets load correctly in production
        plugins: [
            legacy({
                targets: ['defaults', 'not IE 11'],
            }),
            imagetools(),
            react(),
            tailwindcss(),
            compression({
                algorithm: 'gzip',
                ext: '.gz',
                threshold: 10240,
            }),
            compression({
                algorithm: 'brotliCompress',
                ext: '.br',
                threshold: 10240,
            }),
            VitePWA({
                registerType: "autoUpdate",
                injectRegister: "auto",
                includeAssets: ['offline.html', 'manifest.webmanifest', 'index.html'],
                manifest: {
                    name: "Allotment",
                    short_name: "Allotment",
                    start_url: "/",
                    display: "standalone",
                    background_color: "#ffffff",
                    theme_color: "#007333",
                },
                workbox: {
                    navigateFallback: '/index.html',
                    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
                    runtimeCaching: [
                        {
                            urlPattern: ({ url }) => url.pathname.startsWith('/api'),
                            handler: 'NetworkFirst',
                            options: {
                                cacheName: 'api-cache',
                                expiration: {
                                    maxEntries: 50,
                                    maxAgeSeconds: 60 * 60 * 24, // 1 day
                                },
                            },
                        },
                        {
                            urlPattern: /\.(png|jpg|jpeg|svg|gif|ico)$/,
                            handler: 'CacheFirst',
                            options: {
                                cacheName: 'images-cache',
                                expiration: {
                                    maxEntries: 60,
                                    maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
                                },
                            },
                        },
                        {
                            urlPattern: /\.(js|css)$/,
                            handler: 'StaleWhileRevalidate',
                            options: {
                                cacheName: 'static-resources',
                            },
                        },
                        {
                            urlPattern: /^https:\/\/fonts/,
                            handler: 'CacheFirst',
                            options: {
                                cacheName: 'fonts-cache',
                                expiration: {
                                    maxEntries: 30,
                                    maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
                                },
                            },
                        },
                    ],
                },
            }),
        ],
        optimizeDeps: {
            include: ['react', 'react-dom'],
            exclude: ['lucide-react'], // Allow tree-shaking for icons
        },
        resolve: {
            alias: {
                "@": path.resolve(process.cwd(), "src"),
            },
            dedupe: ['react', 'react-dom'],
        },
        build: {
            sourcemap: false,
            cssCodeSplit: false,
            minify: 'terser' as const,
            terserOptions: {
                compress: {
                    drop_console: true,
                    drop_debugger: true,
                    pure_funcs: ['console.log', 'console.debug', 'console.info'], // Remove specific console methods
                    passes: 2, // Multiple passes for better compression
                },
                mangle: {
                    safari10: true, // Better Safari compatibility
                },
            },
            chunkSizeWarningLimit: 800, // Reduced from 1000 to encourage smaller chunks
            assetsInlineLimit: 4096, // Inline smaller assets as base64
            rollupOptions: {
                output: {
                    manualChunks(id) {
                        // Ensure React and closely-related router/runtime packages are isolated into
                        // a single chunk to avoid circular ESM evaluation issues where other vendor
                        // chunks import back into the React runtime before it's initialized.
                        // Use a cross-platform regex to match both POSIX and Windows paths.
                        const reactPkgRe = /node_modules[\\\/](?:react|react-dom|react-router|react-router-dom|react-is|next-themes|@tanstack|@hookform|react-window|react-hook-form)[\\\/]/;
                        if (reactPkgRe.test(id)) {
                            return 'react-vendor';
                        }

                        // UI Library chunks
                        if (id.includes('node_modules/@radix-ui/')) {
                            return '@radix-ui';
                        }

                        // Utility libraries
                        if (id.includes('node_modules/zod') || id.includes('node_modules/tailwind-merge') || id.includes('node_modules/class-variance-authority')) {
                            return 'utils';
                        }

                        // Icons - keep as separate chunk for caching
                        if (id.includes('node_modules/lucide-react')) {
                            return 'vendor_lucide';
                        }

                        // Large data libraries
                        if (id.includes('node_modules/countries-list')) {
                            return 'countries-list';
                        }

                        // HTTP client
                        if (id.includes('node_modules/axios')) {
                            return 'axios';
                        }

                        // Notifications and UI effects
                        if (id.includes('node_modules/sonner') || id.includes('node_modules/cmdk')) {
                            return 'ui-effects';
                        }

                        // PWA and service workers
                        if (id.includes('node_modules/workbox-')) {
                            return 'workbox';
                        }

                        // Other node_modules - group remaining smaller libraries into vendor-misc.
                        if (id.includes('node_modules/')) {
                            const pkg = id.split('node_modules/')[1].split('/')[0];
                            const skip = ['detect-node-es', 'set-cookie-parser', 'turbo-stream'];
                            if (skip.includes(pkg)) {
                                return; // keep in main bundle
                            }
                            return 'vendor-misc';
                        }
                    },
                },
            },
        },
        server: {
            host: true, // Listen on all addresses for Docker
            port: 5173,
        },
    };
});