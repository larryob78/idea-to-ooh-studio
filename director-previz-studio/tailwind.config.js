/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0A0A0A',
        panel: '#1C1C1E',
        accent: '#FF6B00',
      },
      borderRadius: {
        glass: '12px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      transitionDuration: {
        300: '300ms',
      },
      boxShadow: {
        glow: '0 0 24px rgba(255,107,0,0.25)',
      },
    },
  },
  plugins: [],
};
