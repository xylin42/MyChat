import {defineConfig} from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    base: '/vite/',
    server: {
        allowedHosts: true,
        strictPort: true,
    },
    plugins: [
        tailwindcss(),
    ],
    build: {
        rollupOptions: {
            input: 'static/main.js',
        },
        outDir: 'static/dist',
        manifest: true,
    }
})
