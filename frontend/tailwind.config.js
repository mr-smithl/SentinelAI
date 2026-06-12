/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sentinel: {
          green: '#1D9E75',
          amber: '#BA7517',
          red: '#E24B4A',
          purple: '#534AB7',
        },
      },
    },
  },
  plugins: [],
}
