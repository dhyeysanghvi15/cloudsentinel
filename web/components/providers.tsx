"use client";

import { ToastCenter } from "./toast";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <ToastCenter />
    </>
  );
}
