import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    strictPort: true,
    port: 8081,
    proxy: {
      "/api": {
        target: "http://message-refiner-service:8080",
        changeOrigin: true,
      },
    },
  },
});
