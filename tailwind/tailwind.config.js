/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../templates/*.html',
    '../static/**/*.js',
  ],

  darkMode: 'class',

  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', '"Cascadia Code"', '"Courier New"', 'monospace'],
        ui:   ['"DM Sans"', '"Segoe UI"', 'system-ui', 'sans-serif'],
      },

      colors: {
        base:     'var(--bg-base)',
        surface:  'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        border:   'var(--bg-border)',
        hover:    'var(--bg-hover)',

        accent: {
          DEFAULT: 'var(--accent)',
          hover:   'var(--accent-hover)',
          dim:     'var(--accent-dim)',
          glow:    'var(--accent-glow)',
        },

        primary:   'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        muted:     'var(--text-muted)',

        success: 'var(--success)',
        danger:  'var(--danger)',
        warning: 'var(--warning)',
      },

      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },

      boxShadow: {
        sm:   'var(--shadow-sm)',
        md:   'var(--shadow-md)',
        lg:   'var(--shadow-lg)',
        glow: 'var(--shadow-glow)',
      },
    },
  },

  plugins: [
    require('@tailwindcss/typography'),
  ],
};