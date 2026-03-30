/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                serif: ['"Gowun Batang"', 'serif'],
                gmarket: ['"GmarketSans"', 'sans-serif'],
                western: ['Cinzel', 'Hahmlet', 'serif'],
                eastern: ['JoseonPalace', 'serif'],
            }
        },
    },
    plugins: [],
}
