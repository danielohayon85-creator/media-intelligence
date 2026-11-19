"use client";

import { useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";

import { InsightCard } from "@/components/dashboard/insight-card";
import { DateRangeSelect, dateRangeFromDays } from "@/components/filters/date-range-select";
import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { useDashboardData } from "@/lib/use-dashboard-data";

export default function InsightsPage() {
  const { organizationId } = useOrg();
  const [days, setDays] = useState(30);
  const { insights, loading } = useDashboardData(organizationId, days);
  const [localInsights, setLocalInsights] = useState<typeof insights | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const displayed = localInsights ?? insights;

  async function handleRefresh() {
    if (!organizationId) return;
    setRefreshing(true);
    try {
      const { dateFrom, dateTo } = dateRangeFromDays(days);
      const fresh = await api.refreshInsights({ organizationId, dateFrom, dateTo });
      setLocalInsights(fresh);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <>
      <Topbar title="תובנות AI" subtitle="תובנות תיאוריות, השוואתיות, פרשניות ואופרטיביות" />
      <main className="flex-1 space-y-4 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <DateRangeSelect
            days={days}
            onChange={(d) => {
              setDays(d);
              setLocalInsights(null);
            }}
          />
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            הפקת תובנות מחדש
          </Button>
        </div>

        {loading && displayed.length === 0 ? (
          <Loader2 className="h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
        ) : displayed.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">
            אין מספיק נתונים בתקופה הנבחרת כדי להפיק תובנות.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {displayed.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
