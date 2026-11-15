import React from "react";
import "./globals.css";

export const metadata = {
  title: "Customer Support Resolution Agent",
  description: "Omnichannel Text & Voice Support Agent with Deterministic Approval Gate",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}