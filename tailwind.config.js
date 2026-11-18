/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.html",
        "./**/templates/**/*.html",
        "./static/**/*.js",
    ],

    theme: {
        extend: {
            fontFamily: {
                sans: ['Vazirmatn', 'system-ui', 'sans-serif'],
            },

            colors: {
                background: '#f5f6f9',
                foreground: '#1d2433',
                surface: '#ffffff',
                'surface-muted': '#eef0f5',
                card: '#ffffff',

                primary: {
                    DEFAULT: '#1f4e79',
                    dark: '#173a5e',
                    foreground: '#ffffff',
                },

                secondary: {
                    DEFAULT: '#2b3140',
                    foreground: '#ffffff',
                },

                muted: {
                    DEFAULT: '#eef0f5',
                    foreground: '#5b6478',
                },

                accent: {
                    DEFAULT: '#d98e04',
                    foreground: '#1d2433',
                },

                border: '#e2e5ec',
            },

            boxShadow: {
                soft: '0 1px 2px rgba(20,35,60,.04), 0 4px 16px rgba(20,35,60,.06)',
                elevated: '0 4px 12px rgba(20,35,60,.08), 0 16px 40px rgba(20,35,60,.10)',
                glow: '0 8px 32px rgba(31,78,121,.25)',
            },

            keyframes: {
                'fade-up': {
                    '0%': {
                        opacity: 0,
                        transform: 'translateY(12px)',
                    },
                    '100%': {
                        opacity: 1,
                        transform: 'translateY(0)',
                    },
                },

                'pulse-dot': {
                    '0%,80%,100%': {
                        opacity: 0.3,
                        transform: 'scale(.8)',
                    },
                    '40%': {
                        opacity: 1,
                        transform: 'scale(1)',
                    },
                },
            },

            animation: {
                'fade-up': 'fade-up .6s ease-out both',
            },
        },
    },

    plugins: [],
};
