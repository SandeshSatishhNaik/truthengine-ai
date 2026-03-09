/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        card: "#111827",
        accent: {
          DEFAULT: "#8b5cf6",
          blue: "#3b82f6",
        },
      },
      backgroundImage: {
        "gradient-accent": "linear-gradient(135deg, #8b5cf6, #3b82f6)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
