"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  // Static-export friendly redirect.
  // (Server redirects can be unsupported in `output: "export"`.)
  const router = useRouter();
  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);
  return null;
}
