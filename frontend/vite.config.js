import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const flask = { target: "http://127.0.0.1:5000", changeOrigin: false };
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": flask, "/admin": flask } },
});