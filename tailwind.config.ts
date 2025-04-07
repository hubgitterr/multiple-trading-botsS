import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}", // Ensure app directory is included
  ],
  darkMode: "class", // Enable dark mode using a class strategy
  theme: {
    extend: {
      // Keep existing extensions if any, or add new ones like colors
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      // Add custom theme colors for light/dark modes
      colors: {
        // Example Light Mode Colors (Customize as needed)
        primary: {
          light: '#3b82f6', // Blue 500
          DEFAULT: '#2563eb', // Blue 600
          dark: '#1d4ed8', // Blue 700
        },
        secondary: {
          light: '#f9fafb', // Gray 50
          DEFAULT: '#f3f4f6', // Gray 100
          dark: '#e5e7eb', // Gray 200
        },
        background: {
          light: '#ffffff', // White
          DEFAULT: '#f9fafb', // Gray 50
        },
        text: {
          primary: '#1f2937', // Gray 800
          secondary: '#6b7280', // Gray 500
        },
        // Example Dark Mode Colors (Customize as needed)
        // These might be used like: dark:bg-dark-background dark:text-dark-text-primary
        dark: {
          primary: {
            light: '#60a5fa', // Blue 400
            DEFAULT: '#3b82f6', // Blue 500
            dark: '#2563eb', // Blue 600
          },
          secondary: {
            light: '#374151', // Gray 700
            DEFAULT: '#1f2937', // Gray 800
            dark: '#111827', // Gray 900
          },
          background: {
            light: '#1f2937', // Gray 800
            DEFAULT: '#111827', // Gray 900
          },
          text: {
            primary: '#f9fafb', // Gray 50
            secondary: '#9ca3af', // Gray 400
          },
        }
      },
    },
  },
  plugins: [], // Add any Tailwind plugins here if needed later
};
export default config;
