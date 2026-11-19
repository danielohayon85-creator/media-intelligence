"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2, Search } from "lucide-react";

import { DedupBadge, RelevanceBadge, SentimentBadge } from "@/components/items/badges";
import { DateRangeSelect, dateRangeFromDays } from "@/components/filters/date-range-select";
import { Topbar } from "@/components/layout/topbar";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { api, type MediaItem } from "@/lib/api";
import { useOrg } from "@/lib/org-context";

const PAGE_SIZE = 20;

export default function ItemsPage() {
  const { organizationId } = useOrg();
  const [days, setDays] = useState(30);
  const [sentiment, setSentiment] = useState("");
  const [mediaType, setMediaType] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<MediaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!organizationId) return;
    let cancelled = false;
    const { dateFrom, dateTo } = dateRangeFromDays(days);

    setLoading(true);
    setError(null);
    api
      .listItems({
        organizationId,
        dateFrom,
        dateTo,
        sentiment: sentiment || undefined,
        mediaType: mediaType || undefined,
        search: search || undefined,
        page,
        pageSize: PAGE_SIZE,
      })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
      })
      .catch(() => !cancelled && setError("שגיאה בטעינת פרסומים."))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [organizationId, days, sentiment, mediaType, search, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <>
      <Topbar title="סיקור ופרסומים" subtitle={`${total} פרסומים בתקופה הנבחרת`} />
      <main className="flex-1 space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <DateRangeSelect
            days={days}
            onChange={(d) => {
              setDays(d);
              setPage(1);
            }}
          />
          <Select
            value={sentiment}
            onChange={(e) => {
              setSentiment(e.target.value);
              setPage(1);
            }}
          >
            <option value="">כל הסנטימנטים</option>
            <option value="positive">חיובי</option>
            <option value="negative">שלילי</option>
            <option value="neutral">ניטרלי</option>
            <option value="mixed">מעורב</option>
          </Select>
          <Select
            value={mediaType}
            onChange={(e) => {
              setMediaType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">כל סוגי המדיה</option>
            <option value="online">אונליין</option>
            <option value="print">עיתונות מודפסת</option>
            <option value="tv">טלוויזיה</option>
            <option value="radio">רדיו</option>
            <option value="social">רשתות חברתיות</option>
          </Select>
          <div className="relative">
            <Search className="pointer-events-none absolute right-2.5 top-2.5 h-4 w-4 text-[var(--muted-foreground)]" />
            <Input
              placeholder="חיפוש בכותרת…"
              className="w-56 pr-8"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </div>

        {error && <p className="text-sm text-[var(--danger-fg)]">{error}</p>}

        <div className="overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--card)]">
          <table className="w-full text-sm">
            <thead className="border-b border-[var(--border)] text-[var(--muted-foreground)]">
              <tr>
                <th className="px-4 py-2 text-right font-medium">כותרת</th>
                <th className="px-4 py-2 text-right font-medium">כלי תקשורת</th>
                <th className="px-4 py-2 text-right font-medium">תאריך</th>
                <th className="px-4 py-2 text-right font-medium">סנטימנט</th>
                <th className="px-4 py-2 text-right font-medium">רלוונטיות</th>
                <th className="px-4 py-2 text-right font-medium">סטטוס</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-[var(--muted-foreground)]">
                    <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                  </td>
                </tr>
              )}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-[var(--muted-foreground)]">
                    אין פרסומים התואמים את הסינון הנבחר.
                  </td>
                </tr>
              )}
              {!loading &&
                items.map((item) => (
                  <tr key={item.id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--muted)]/50">
                    <td className="max-w-md px-4 py-2.5">
                      <Link href={`/items/${item.id}`} className="font-medium hover:text-[var(--primary)]">
                        {item.title}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 text-[var(--muted-foreground)]">{item.outlet_name}</td>
                    <td className="px-4 py-2.5 text-[var(--muted-foreground)]">
                      {new Date(item.published_at).toLocaleDateString("he-IL")}
                    </td>
                    <td className="px-4 py-2.5">
                      {item.analysis && <SentimentBadge sentiment={item.analysis.sentiment} />}
                    </td>
                    <td className="px-4 py-2.5">
                      {item.analysis && <RelevanceBadge relevance={item.analysis.relevance} />}
                    </td>
                    <td className="px-4 py-2.5">
                      <DedupBadge role={item.dedup_role} />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--muted-foreground)]">
            עמוד {page} מתוך {totalPages}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              הקודם
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              הבא
            </Button>
          </div>
        </div>
      </main>
    </>
  );
}
