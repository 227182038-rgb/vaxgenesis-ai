import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: { colors: {
    bg: { DEFAULT: "#0b0c0c", subtle: "#1c1f23", card: "#21262b" },
    accent: { DEFAULT: "#80c3e4", warm: "#c74d61" },
    text: { DEFAULT: "#e9ebeb", muted: "#888e91" },
  }}},
  plugins: [],
};
export default config;
