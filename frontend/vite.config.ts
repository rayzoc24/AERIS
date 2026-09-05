import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react()],
    base: "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    server: {
      port: 5173,
      host: "127.0.0.1",
      strictPort: true,
      proxy: {
        "/api": {
          target: env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000",
          changeOrigin: true,
          secure: false,
        },
        "/ws": {
          target: env.VITE_BACKEND_WS_URL ?? "ws://127.0.0.1:8000",
          ws: true,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: false, // security: do not expose source maps in production
      target: "es2020",
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom", "react-router-dom"],
            query: ["@tanstack/react-query"],
            utils: ["axios", "dompurify", "zustand"],
          },
        },
      },
    },
    define: {
      // Avoid leaking Node env to the browser bundle. Only expose a small set.
      __APP_VERSION__: JSON.stringify(env.npm_package_version ?? "0.1.0"),
    },
  };
});
