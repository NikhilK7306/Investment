"use client";

import { cn } from "@/lib/utils";

interface ToastProps {
  title?: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
  onClose?: () => void;
}

export function Toast({ title, description, variant = "default", onClose }: ToastProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border shadow-lg bg-card",
        variant === "destructive" && "border-red-200 bg-red-50",
        variant === "success" && "border-green-200 bg-green-50"
      )}
    >
      <div className="flex-1">
        {title && <p className="font-medium">{title}</p>}
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      <button
        onClick={onClose}
        className="p-1 rounded hover:bg-muted transition-colors"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

interface ToasterProps {
  toasts: ToastProps[];
}

export function Toaster({ toasts }: ToasterProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast, index) => (
        <Toast key={index} {...toast} />
      ))}
    </div>
  );
}

const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

export { ToastProvider };