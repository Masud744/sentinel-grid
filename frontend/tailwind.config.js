/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        safe: {
          light: '#d1fae5',
          DEFAULT: '#10b981',
          dark: '#065f46',
        },
        warning: {
          light: '#fef3c7',
          DEFAULT: '#f59e0b',
          dark: '#92400e',
        },
        critical: {
          light: '#fee2e2',
          DEFAULT: '#ef4444',
          dark: '#991b1b',
        },
      },
    },
  },
  plugins: [],
}
