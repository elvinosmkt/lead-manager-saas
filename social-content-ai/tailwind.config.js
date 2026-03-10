/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    500: '#E63946',
                },
                dark: {
                    900: '#0A0A0A',
                    800: '#111111',
                    700: '#1a1a1a'
                }
            }
        },
    },
    plugins: [],
}
