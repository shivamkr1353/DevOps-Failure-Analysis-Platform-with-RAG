/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 25px 80px rgba(15, 23, 42, 0.4)"
      }
    }
  },
  plugins: []
}

