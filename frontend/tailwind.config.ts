import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Chakra Petch", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#111827",
        road: "#202124",
        mint: "#111827",
        sky: "#111827",
      },
      boxShadow: {
        panel: "0 20px 60px rgba(17, 24, 39, 0.14)",
      },
    },
  },
  plugins: [],
} satisfies Config;
