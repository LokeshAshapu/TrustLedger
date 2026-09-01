/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          primary: "#0B0D10",
          secondary: "#111419",
          surface: "#171B21",
          hover: "#1F242C",
        },
        border: {
          subtle: "#252B33",
          active: "#3A4350",
          accent: "#4FA3FF",
        },
        text: {
          primary: "#F4F6F8",
          secondary: "#9BA3AE",
          muted: "#626A75",
        },
        verdict: {
          approve: "#43D17A",
          review: "#F3B94A",
          block: "#F05A67",
        },
        accent: {
          ai: "#8B7CFF",
          infra: "#4FA3FF",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
        glowApprove: "0 0 15px -3px rgba(67, 209, 122, 0.25)",
        glowReview: "0 0 15px -3px rgba(243, 185, 74, 0.25)",
        glowBlock: "0 0 15px -3px rgba(240, 90, 103, 0.25)",
        glowAI: "0 0 15px -3px rgba(139, 124, 255, 0.25)",
      },
      borderRadius: {
        card: "12px",
        control: "8px",
      },
    },
  },
  plugins: [],
}
