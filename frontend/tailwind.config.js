/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#E61C5D",
          secondary: "#F6F7FB",
          dark: "#16213E"
        }
      }
    }
  },
  plugins: []
};

