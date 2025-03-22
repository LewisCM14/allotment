import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react-swc';
import { defineConfig } from 'vite';
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Allotment Planner",
        short_name: "Allotment",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#007333",
        icons: [{ src: "/icon.png", sizes: "512x512", type: "image/png" }],
      },
      workbox: {
        runtimeCaching: [{ urlPattern: "/*", handler: "CacheFirst" }],
      },
    }),
  ],
});
