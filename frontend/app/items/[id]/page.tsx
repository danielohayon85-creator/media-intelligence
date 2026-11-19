"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowRight, ExternalLink, Loader2, PencilLine } from "lucide-react";

import {
  COVERAGE_STYLE_LABEL,
  DedupBadge,
  FRAMING_LABEL,
  MEDIA_TYPE_LABEL,
  RelevanceBadge,
  SentimentBadge,
} from "@/components/items/badges";
import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api, type MediaItem } from "@/lib/api";

export default function ItemDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<MediaItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [sentiment, setSentiment] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!params.id) return;
    setLoading(true);
    api
      .getItem(params.id)
      .then((data) => {
        setItem(data);
        setSentiment(data.analysis?.sentiment ?? "");
      })
      .finally(() => setLoading(false));
  }, [params.id]);

  async function saveCorrection() {
    if (!item) return;
    setSaving(true);
    try {
      const updated = await api.correctAnalysis(item.id, {
        sentiment: sentiment || undefined,
        correction_notes: notes || undefined,
      });
      setItem(updated);
      setEditing(false);
      setNotes("");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--muted-foreground)]" />
      </div>
    );
  }

  if (!item) {
    return (
      <>
        <Topbar title="פרסום לא נמצא" />
        <main className="p-6">
          <Link href="/items" className="text-sm text-[var(--primary)]">
            חזרה לרשימת הפרסומים
          </Link>
        </main>
      </>
    );
  }

  return (
    <>
      <Topbar title="פרטי פרסום" subtitle={item.outlet_name} />
      <main className="flex-1 space-y-4 p-6">
        <Link href="/items" className="flex items-center gap-1 text-sm text-[var(--muted-foreground)] hover:text-[var(--primary)]">
          <ArrowRight className="h-3.5 w-3.5" />
          חזרה לרשימת הפרסומים
        </Link>

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              {item.analysis && <SentimentBadge sentiment={item.analysis.sentiment} />}
              {item.analysis && <RelevanceBadge relevance={item.analysis.relevance} />}
              <DedupBadge role={item.dedup_role} />
              <Badge variant="outline">{MEDIA_TYPE_LABEL[item.media_type] ?? item.media_type}</Badge>
            </div>
            <CardTitle className="text-xl font-bold text-[var(--foreground)]">{item.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-4 text-sm text-[var(--muted-foreground)]">
              <span>כלי תקשורת: {item.outlet_name}</span>
              {item.author_name && <span>כתב/ת: {item.author_name}</span>}
              <span>תאריך: {new Date(item.published_at).toLocaleString("he-IL")}</span>
              {item.exposure_count != null && <span>חשיפה משוערת: {item.exposure_count.toLocaleString()}</span>}
              {item.url && (
                <a href={item.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-[var(--primary)]">
                  מקור <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>

            <p className="whitespace-pre-wrap text-sm leading-relaxed">{item.content || item.summary}</p>

            {item.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {item.keywords.map((k) => (
                  <Badge key={k} variant="secondary">
                    {k}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-[var(--foreground)]">ניתוח AI</CardTitle>
              {!editing && (
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  <PencilLine className="h-3.5 w-3.5" />
                  תיקון ידני
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {item.analysis ? (
              <>
                <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-[var(--muted-foreground)]">אופי סיקור</dt>
                    <dd>{COVERAGE_STYLE_LABEL[item.analysis.coverage_style] ?? item.analysis.coverage_style}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--muted-foreground)]">ביטחון רלוונטיות</dt>
                    <dd>{Math.round(item.analysis.relevance_confidence * 100)}%</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--muted-foreground)]">ביטחון סנטימנט</dt>
                    <dd>{Math.round(item.analysis.sentiment_confidence * 100)}%</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--muted-foreground)]">ספק AI</dt>
                    <dd>{item.analysis.ai_provider}</dd>
                  </div>
                </dl>
                {item.analysis.framing.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {item.analysis.framing.map((f) => (
                      <Badge key={f} variant="outline">
                        {FRAMING_LABEL[f] ?? f}
                      </Badge>
                    ))}
                  </div>
                )}
                {item.analysis.manually_corrected && (
                  <p className="rounded-md bg-[var(--muted)] p-2 text-xs text-[var(--muted-foreground)]">
                    סיווג זה תוקן ידנית. {item.analysis.correction_notes}
                  </p>
                )}

                {editing && (
                  <div className="space-y-2 border-t border-[var(--border)] pt-3">
                    <label className="block text-xs font-medium text-[var(--muted-foreground)]">
                      סנטימנט מתוקן
                    </label>
                    <Select value={sentiment} onChange={(e) => setSentiment(e.target.value)}>
                      <option value="positive">חיובי</option>
                      <option value="negative">שלילי</option>
                      <option value="neutral">ניטרלי</option>
                      <option value="mixed">מעורב</option>
                    </Select>
                    <label className="block text-xs font-medium text-[var(--muted-foreground)]">
                      הערת תיקון
                    </label>
                    <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="מדוע התיקון נדרש" />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={saveCorrection} disabled={saving}>
                        {saving ? "שומר…" : "שמירה"}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
                        ביטול
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-[var(--muted-foreground)]">הפריט עדיין בתהליך ניתוח.</p>
            )}
          </CardContent>
        </Card>
      </main>
    </>
  );
}
