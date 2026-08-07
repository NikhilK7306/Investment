import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "IPO Intelligence Agent",
  description: "Autonomous multi-agent AI system for IPO investment intelligence",
  keywords: ["IPO", "investment", "analysis", "AI", "financial research"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased bg-background text-foreground`}>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}