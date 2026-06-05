import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:5050",
      "/send-emails": "http://localhost:5050",
      "/preview-emails": "http://localhost:5050"
    }
  }
});
