import type { Metadata } from "next";
import { Heebo } from "next/font/google";

import { Sidebar } from "@/components/layout/sidebar";
import { ThemeProvider } from "@/components/theme-provider";
import { OrgProvider } from "@/lib/org-context";
import "./globals.css";

const heebo = Heebo({
  variable: "--font-heebo",
  subsets: ["hebrew", "latin"],
});

export const metadata: Metadata = {
  title: "Media Intelligence — מודיעין תקשורתי",
  description: "מערכת תובנות ומודיעין תקשורתי לדוברים ומנהלי תקשורת",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl" className={`${heebo.variable} h-full`} suppressHydrationWarning>
      <body className="min-h-full antialiased">
        <ThemeProvider attribute="data-theme" defaultTheme="system" enableSystem>
          <OrgProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex min-h-screen flex-1 flex-col">{children}</div>
            </div>
          </OrgProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
