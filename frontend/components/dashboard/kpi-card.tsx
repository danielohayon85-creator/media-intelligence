import { ArrowDown, ArrowUp, Minus } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function KpiCard({
  label,
  value,
  suffix,
  deltaPct,
  deltaLabel,
  tone,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  deltaPct?: number | null;
  deltaLabel?: string;
  tone?: "positive" | "negative" | "neutral";
}) {
  const DeltaIcon = deltaPct == null || deltaPct === 0 ? Minus : deltaPct > 0 ? ArrowUp : ArrowDown;
  const isGoodDirection = tone === "negative" ? (deltaPct ?? 0) <= 0 : (deltaPct ?? 0) >= 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <span className="text-2xl font-bold">
            {value}
            {suffix && <span className="mr-1 text-sm font-normal text-[var(--muted-foreground)]">{suffix}</span>}
          </span>
          {deltaPct != null && (
            <span
              className={cn(
                "flex items-center gap-0.5 text-xs font-medium",
                isGoodDirection ? "text-[var(--success-fg)]" : "text-[var(--danger-fg)]"
              )}
            >
              <DeltaIcon className="h-3 w-3" />
              {Math.abs(deltaPct)}%
            </span>
          )}
        </div>
        {deltaLabel && <p className="mt-1 text-xs text-[var(--muted-foreground)]">{deltaLabel}</p>}
      </CardContent>
    </Card>
  );
}
