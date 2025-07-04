/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Standard shadcn/ui colors (required for border-border, etc.)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        
        // Divine color palette (preserved)
        divine: {
          50: '#fdf8f6',
          100: '#f2e8e5',
          200: '#eaddd7',
          300: '#e0cec7',
          400: '#d2bab0',
          500: '#bfa094',
          600: '#a18072',
          700: '#977669',
          800: '#846358',
          900: '#43302b',
        },
        olympus: {
          gold: '#FFD700',
          'gold-light': '#FFF8DC',
          'gold-dark': '#DAA520',
          sky: '#87CEEB',
          'sky-light': '#E0F6FF',
          'sky-dark': '#4682B4',
          thunder: '#4B0082',
          'thunder-light': '#6A0DAD',
          'thunder-dark': '#301860',
          marble: '#F8F8FF',
          'marble-dark': '#E8E8F0',
        },
        zeus: {
          primary: '#4B0082',    // Deep purple (thunder)
          secondary: '#FFD700',  // Gold
          accent: '#87CEEB',     // Sky blue
          dark: '#1a1a2e',       // Dark background
          light: '#F8F8FF',      // Light marble
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        divine: ['Cinzel', 'serif'],
        olympian: ['Philosopher', 'sans-serif'],
        ancient: ['Uncial Antiqua', 'cursive'],
      },
      backgroundImage: {
        'divine-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'olympus-gradient': 'linear-gradient(to bottom, #87CEEB 0%, #E0F6FF 50%, #F8F8FF 100%)',
        'thunder-gradient': 'radial-gradient(circle at center, #6A0DAD 0%, #4B0082 50%, #301860 100%)',
        'gold-shimmer': 'linear-gradient(45deg, #FFD700 0%, #FFF8DC 50%, #FFD700 100%)',
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        'divine-glow': 'divineGlow 2s ease-in-out infinite',
        'thunder-strike': 'thunderStrike 0.5s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        divineGlow: {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(255, 215, 0, 0.5), 0 0 40px rgba(255, 215, 0, 0.3)',
          },
          '50%': {
            boxShadow: '0 0 30px rgba(255, 215, 0, 0.8), 0 0 60px rgba(255, 215, 0, 0.5)',
          },
        },
        thunderStrike: {
          '0%': {
            opacity: '0',
            transform: 'scaleY(0)',
          },
          '50%': {
            opacity: '1',
            transform: 'scaleY(1)',
          },
          '100%': {
            opacity: '0',
            transform: 'scaleY(0)',
          },
        },
        float: {
          '0%, 100%': {
            transform: 'translateY(0)',
          },
          '50%': {
            transform: 'translateY(-10px)',
          },
        },
        shimmer: {
          '0%': {
            backgroundPosition: '-1000px 0',
          },
          '100%': {
            backgroundPosition: '1000px 0',
          },
        },
      },
      boxShadow: {
        'divine': '0 4px 20px rgba(255, 215, 0, 0.3)',
        'divine-lg': '0 10px 40px rgba(255, 215, 0, 0.4)',
        'thunder': '0 0 20px rgba(75, 0, 130, 0.5)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}