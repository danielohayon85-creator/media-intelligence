"use client";

import { useEffect, useState } from "react";

import { api, type DataQualityResponse, type Insight, type KpiResponse, type TrendResponse } from "@/lib/api";
import { dateRangeFromDays } from "@/components/filters/date-range-select";

export function useDashboardData(organizationId: string | null, days: number) {
  const [kpis, setKpis] = useState<KpiResponse | null>(null);
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [quality, setQuality] = useState<DataQualityResponse | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!organizationId) return;
    const orgId = organizationId;
    let cancelled = false;
    const { dateFrom, dateTo } = dateRangeFromDays(days);

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const [kpisRes, trendRes, qualityRes, insightsRes] = await Promise.all([
          api.getKpis({ organizationId: orgId, dateFrom, dateTo }),
          api.getTrend({ organizationId: orgId, dateFrom, dateTo }),
          api.getDataQuality(orgId),
          api.getInsights({ organizationId: orgId, dateFrom, dateTo }),
        ]);
        if (cancelled) return;
        setKpis(kpisRes);
        setTrend(trendRes);
        setQuality(qualityRes);
        setInsights(insightsRes);
      } catch {
        if (!cancelled) setError("שגיאה בטעינת נתוני הדשבורד מהשרת.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [organizationId, days]);

  return { kpis, trend, quality, insights, loading, error };
}
