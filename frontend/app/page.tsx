"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { DataQualityStrip } from "@/components/dashboard/data-quality-strip";
import { InsightCard } from "@/components/dashboard/insight-card";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { DemoBanner } from "@/components/demo-banner";
import { EmptyStateSeed } from "@/components/empty-state-seed";
import { DateRangeSelect } from "@/components/filters/date-range-select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Topbar } from "@/components/layout/topbar";
import { useDashboardData } from "@/lib/use-dashboard-data";
import { useOrg } from "@/lib/org-context";

export default function DashboardPage() {
  const { organizations, organizationId, loading: orgLoading } = useOrg();
  const [days, setDays] = useState(30);
  const { kpis, trend, quality, insights, loading } = useDashboardData(organizationId, days);

  const currentOrg = organizations.find((o) => o.id === organizationId);
  const operationalInsight = insights.find((i) => i.level === "operational");
  const descriptiveInsight = insights.find((i) => i.level === "descriptive");

  if (orgLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--muted-foreground)]" />
      </div>
    );
  }

  if (!organizations.length) {
    return (
      <>
        <Topbar title="תמונת מצב" subtitle="סקירה תקשורתית" />
        <EmptyStateSeed />
      </>
    );
  }

  return (
    <>
      <Topbar title="תמונת מצב" subtitle={currentOrg?.name} />
      <main className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {currentOrg?.is_demo ? <DemoBanner /> : <div />}
          <DateRangeSelect days={days} onChange={setDays} />
        </div>

        {(descriptiveInsight || operationalInsight) && (
          <Card className="border-[var(--primary)]/30">
            <CardHeader>
              <CardTitle className="text-base font-bold text-[var(--foreground)]">
                מה חשוב לדעת היום?
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {descriptiveInsight && (
                <p className="text-sm">
                  <span className="font-semibold">מה קרה: </span>
                  {descriptiveInsight.explanation}
                </p>
              )}
              {operationalInsight && (
                <p className="text-sm">
                  <span className="font-semibold">פעולה מומלצת: </span>
                  {operationalInsight.recommendation || operationalInsight.explanation}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            label="אזכורים תקשורתיים"
            value={kpis?.total_mentions ?? "—"}
            deltaPct={kpis?.change_vs_previous_period_pct ?? null}
            deltaLabel="לעומת התקופה הקודמת"
          />
          <KpiCard label="פרסומים ייחודיים" value={kpis?.unique_publications ?? "—"} />
          <KpiCard
            label="סיקור שלילי"
            value={kpis?.negative_pct ?? "—"}
            suffix="%"
            tone="negative"
          />
          <KpiCard label="סיקור חיובי" value={kpis?.positive_pct ?? "—"} suffix="%" tone="positive" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-[var(--foreground)]">
              מגמת סיקור יומית
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart points={trend?.points ?? []} />
          </CardContent>
        </Card>

        <div>
          <h2 className="mb-3 text-base font-bold">תובנות AI</h2>
          {loading && insights.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)]">טוען תובנות…</p>
          ) : insights.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)]">
              אין מספיק נתונים בתקופה הנבחרת כדי להפיק תובנות.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {insights.map((insight) => (
                <InsightCard key={insight.id} insight={insight} />
              ))}
            </div>
          )}
        </div>

        {quality && <DataQualityStrip data={quality} />}
      </main>
    </>
  );
}
