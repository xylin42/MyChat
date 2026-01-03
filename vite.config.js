import {defineConfig} from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
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
