/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep Ocean Palette
        abyss: '#050a12',
        deep: '#0a1018',
        surface: '#111a27',
        card: {
          DEFAULT: '#162030',
          hover: '#1c2940',
        },
        // Eco-Tech Accents
        primary: {
          DEFAULT: '#22c55e',
          dim: 'rgba(34, 197, 94, 0.15)',
          glow: 'rgba(34, 197, 94, 0.4)',
        },
        secondary: '#06b6d4',
        tertiary: '#8b5cf6',
        warning: '#f59e0b',
        danger: '#ef4444',
        pink: '#ec4899',
        // Text colors
        bright: '#f8fafc',
        muted: '#64748b',
      },
      fontFamily: {
        heading: ['Syne', 'sans-serif'],
        sans: ['DM Sans', '-apple-system', 'sans-serif'],
      },
      spacing: {
        'xs': '0.25rem',
        'sm': '0.5rem',
        'md': '1rem',
        'lg': '1.5rem',
        'xl': '2rem',
        '2xl': '3rem',
      },
      borderRadius: {
        'sm': '6px',
        'md': '10px',
        'lg': '16px',
        'xl': '24px',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        'fast': '150ms',
        'base': '250ms',
        'slow': '400ms',
      },
      boxShadow: {
        'glow-primary': '0 0 40px rgba(34, 197, 94, 0.12)',
        'glow-secondary': '0 0 40px rgba(6, 182, 212, 0.12)',
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
        'scale-in': 'scale-in 0.4s ease-out forwards',
        'pulse-glow': 'pulse-glow 12s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'pulse-glow': {
          '0%': { opacity: '0.6', transform: 'scale(1)' },
          '100%': { opacity: '1', transform: 'scale(1.15)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
