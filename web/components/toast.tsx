"use client";

import { useEffect, useMemo, useState } from "react";
import { setMode } from "./mode";

type ToastAction = "switch-demo" | "none";

type ToastEventDetail = {
  message: string;
  action?: ToastAction;
};

type Toast = {
  id: string;
  message: string;
  action: ToastAction;
};

function nowId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function pushToast(detail: ToastEventDetail) {
  window.dispatchEvent(new CustomEvent<ToastEventDetail>("cloudsentinel:toast", { detail }));
}

export function ToastCenter() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const onToast = (ev: Event) => {
      const e = ev as CustomEvent<ToastEventDetail>;
      const message = String(e.detail?.message || "");
      if (!message) return;
      const toast: Toast = { id: nowId(), message, action: e.detail?.action || "none" };
      setToasts((prev) => [...prev, toast].slice(-3));
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 6000);
    };
    window.addEventListener("cloudsentinel:toast", onToast);
    return () => window.removeEventListener("cloudsentinel:toast", onToast);
  }, []);

  const visible = useMemo(() => toasts.filter(Boolean), [toasts]);
  if (!visible.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] grid w-[360px] gap-2">
      {visible.map((t) => (
        <div key={t.id} className="rounded-xl border border-slate-800 bg-slate-950 p-3 shadow-xl">
          <div className="text-sm text-slate-200">{t.message}</div>
          {t.action === "switch-demo" ? (
            <div className="mt-2">
              <button
                onClick={() => setMode("demo")}
                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
              >
                Switch to Demo Mode
              </button>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

