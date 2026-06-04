import type { Metadata } from "next";
import { Geist, Geist_Mono, Newsreader } from "next/font/google";
import "./globals.css";
import { DemoUserProvider } from "@/hooks/useDemoUser";
import DesktopWidget from "@/components/DesktopWidget";
import { DemoLogin } from "@/components/DemoLogin";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  display: "swap",
  style: ["normal", "italic"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Avatario — The AI receptionist that answers your client calls",
  description:
    "Avatario receives and answers client calls and messages 24/7 — booking appointments, qualifying enquiries, routing urgent cases and following up. Voice-first, multilingual, in English and 9 Indian languages.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${newsreader.variable} antialiased`}
      >
        <DemoUserProvider>
          {children}
          <DemoLogin />
          {/* Floating Desktop Widget - appears on all pages */}
          <DesktopWidget />
        </DemoUserProvider>
      </body>
    </html>
  );
}
