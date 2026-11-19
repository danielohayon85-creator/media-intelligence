import { Lightbulb, type LucideIcon, BarChart3, GitCompare, Search, Target } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Insight } from "@/lib/api";

const LEVEL_META: Record<Insight["level"], { label: string; icon: LucideIcon }> = {
  descriptive: { label: "תיאורית", icon: BarChart3 },
  comparative: { label: "השוואתית", icon: GitCompare },
  interpretive: { label: "פרשנית", icon: Search },
  operational: { label: "אופרטיבית", icon: Target },
};

export function InsightCard({ insight }: { insight: Insight }) {
  const meta = LEVEL_META[insight.level];
  const Icon = meta.icon;

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--muted)]">
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex-1 space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="secondary">{meta.label}</Badge>
              <span className="text-[11px] text-[var(--muted-foreground)]">
                רמת ביטחון {Math.round(insight.confidence * 100)}%
              </span>
            </div>
            <h3 className="text-sm font-bold">{insight.title}</h3>
            <p className="text-sm text-[var(--muted-foreground)]">{insight.explanation}</p>
            {insight.recommendation && (
              <p className="flex items-start gap-1.5 rounded-md bg-[var(--muted)] p-2 text-xs">
                <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--warning-fg)]" />
                <span>{insight.recommendation}</span>
              </p>
            )}
            <p className="text-[11px] text-[var(--muted-foreground)]">
              מבוסס על {insight.supporting_item_ids.length} פרסומים · ספק: {insight.ai_provider}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
