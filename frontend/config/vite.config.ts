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
        },
        resolve: {
            alias: {
                "@": path.resolve(__dirname, "../src"),
            },
            dedupe: ['react', 'react-dom'],
        },
        build: {
            rollupOptions: {
                output: {
                    manualChunks(id) {
                        // isolate lucide-react into its own chunk
                        if (id.includes('node_modules/lucide-react')) {
                            return 'vendor_lucide';
                        }
                        // only split other node_modules
                        if (!id.includes('node_modules')) {
                            return;
                        }
                        const pkg = id.split('node_modules/')[1].split('/')[0];
                        const skip = ['detect-node-es', 'react-router-dom', 'set-cookie-parser', 'turbo-stream'];
                        if (skip.includes(pkg)) {
                            return;
                        }
                        return pkg;
                    },
                },
            },
            sourcemap: false,
            cssCodeSplit: false,
            minify: 'terser' as const,
            terserOptions: {
                compress: {
                    drop_console: true,
                    drop_debugger: true,
                },
                mangle: true,
            },
            chunkSizeWarningLimit: 1000,
        },
    };
});