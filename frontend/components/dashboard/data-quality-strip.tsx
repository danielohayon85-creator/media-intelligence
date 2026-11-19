import { CheckCircle2, Clock, Copy, FileWarning, ListTodo } from "lucide-react";

import type { DataQualityResponse } from "@/lib/api";

function formatDateTime(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
}

export function DataQualityStrip({ data }: { data: DataQualityResponse }) {
  const items: { icon: typeof Clock; label: string; value: string }[] = [
    { icon: Clock, label: "סנכרון אחרון", value: formatDateTime(data.last_synced_at) },
    { icon: CheckCircle2, label: "נקלטו בריצות האחרונות", value: String(data.items_new) },
    { icon: Copy, label: "כפילויות שנמנעו", value: String(data.items_duplicate) },
    { icon: ListTodo, label: "ממתינים לניתוח", value: String(data.items_pending_analysis) },
    { icon: FileWarning, label: "תוכן מלא", value: `${data.items_with_full_content_pct}%` },
  ];

  return (
    <div className="flex flex-wrap gap-4 rounded-lg border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-xs">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 text-[var(--muted-foreground)]">
          <item.icon className="h-3.5 w-3.5" />
          <span>{item.label}:</span>
          <span className="font-semibold text-[var(--foreground)]">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
