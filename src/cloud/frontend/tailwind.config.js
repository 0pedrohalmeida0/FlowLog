/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        flowlog: {
          primary: '#1f6feb',
          secondary: '#586069',
          danger: '#cf222e',
        },
      },
    },
  },
  plugins: [],
}
