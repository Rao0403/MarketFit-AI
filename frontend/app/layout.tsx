import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MarketFit-AI Dashboard",
  description: "Role-based project recommendations from market JD analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
