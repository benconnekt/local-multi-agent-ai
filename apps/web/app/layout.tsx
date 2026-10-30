import type { Metadata } from "next";
import "./globals.css";
import StudioNavigation from "@/components/StudioNavigation";
export const metadata: Metadata = { title: "Local Agent Studio", description: "Local multi-agent workspace" };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><StudioNavigation />{children}</body></html>;
}
