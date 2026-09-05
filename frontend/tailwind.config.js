/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // High-contrast, utilitarian palette. No purple. No gradients.
        aeris: {
          bg: "#0a0a0a",
          surface: "#141414",
          surfaceAlt: "#1c1c1c",
          border: "#2a2a2a",
          textPrimary: "#f4f4f5",
          textSecondary: "#a1a1aa",
          textMuted: "#71717a",
          accent: "#e63946",
          success: "#16a34a",
          warning: "#ca8a04",
          danger: "#dc2626",
          info: "#0ea5e9",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      borderRadius: {
        // Sharp corners. Slight radius only for panels.
        none: "0",
        sm: "2px",
        DEFAULT: "4px",
        lg: "6px",
      },
      boxShadow: {
        // Subtle shadows only.
        sm: "0 1px 2px rgba(0, 0, 0, 0.15)",
        DEFAULT: "0 2px 4px rgba(0, 0, 0, 0.2)",
        lg: "0 4px 8px rgba(0, 0, 0, 0.25)",
      },
      maxWidth: {
        content: "1280px",
      },
    },
  },
  plugins: [],
};
