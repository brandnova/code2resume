/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Root templates folder and all per-app template folders
    '../templates/**/*.html',
    '../templates/*.html',
    
    // Inline Alpine.js and vanilla JS expressions in static files
    '../static/**/*.js',
  ],

  // Dark mode enabled by default (class strategy allows future light mode toggle)
  darkMode: 'class',

  theme: {
    extend: {},
  },

  plugins: [
    // Typography for rich text content (CKEditor)
    require('@tailwindcss/typography'),
  ],
};