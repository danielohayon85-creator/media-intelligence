import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // האפליקציה היא דשבורד דינמי שמביא נתונים מה-API בצד הלקוח (לא SSR/ISR),
  // ולכן Cache Components (prerendering קפדני) מכבה כאן.
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
