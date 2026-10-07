import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {title: "YouTube Analytics · Sign in", robots: {index: false, follow: false}};
export default function RootLayout({children}: {children: ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}
