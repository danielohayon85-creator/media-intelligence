"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Plus, RefreshCw, Upload } from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api, type SourceConnection } from "@/lib/api";
import { useOrg } from "@/lib/org-context";

const SOURCE_TYPE_LABEL: Record<SourceConnection["source_type"], string> = {
  csv: "קובץ CSV",
  json: "קובץ JSON",
  api_generic: "API חיצוני",
  demo: "נתוני הדגמה",
};

export default function SourcesPage() {
  const { organizationId } = useOrg();
  const [sources, setSources] = useState<SourceConnection[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  async function refresh() {
    if (!organizationId) return;
    setLoading(true);
    try {
      setSources(await api.listSources(organizationId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organizationId]);

  return (
    <>
      <Topbar title="הגדרות וחיבורי API" subtitle="ניהול מקורות נתונים" />
      <main className="flex-1 space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--muted-foreground)]">
            חברו מקור CSV/JSON לייבוא חד-פעמי, או הגדירו Adapter גנרי ל-API של ספק ניטור. חיבור ספק
            אמיתי בעתיד דורש עדכון הגדרות בלבד, לא שינוי קוד.
          </p>
          <Button onClick={() => setShowForm((v) => !v)}>
            <Plus className="h-4 w-4" />
            מקור חדש
          </Button>
        </div>

        {showForm && organizationId && (
          <NewSourceForm
            organizationId={organizationId}
            onCreated={() => {
              setShowForm(false);
              refresh();
            }}
          />
        )}

        {loading ? (
          <Loader2 className="h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
        ) : sources.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">אין מקורות מוגדרים עדיין.</p>
        ) : (
          <div className="space-y-3">
            {sources.map((source) => (
              <SourceRow key={source.id} source={source} onChanged={refresh} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}

function SourceRow({ source, onChanged }: { source: SourceConnection; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSync() {
    setBusy(true);
    try {
      await api.syncSource(source.id);
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      await api.ingestFile(source.id, source.source_type as "csv" | "json", file);
      onChanged();
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{source.name}</span>
            <Badge variant="secondary">{SOURCE_TYPE_LABEL[source.source_type]}</Badge>
            {!source.is_active && <Badge variant="outline">לא פעיל</Badge>}
          </div>
          <p className="mt-1 text-xs text-[var(--muted-foreground)]">
            סנכרון אחרון:{" "}
            {source.last_synced_at ? new Date(source.last_synced_at).toLocaleString("he-IL") : "עדיין לא סונכרן"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {(source.source_type === "csv" || source.source_type === "json") && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept={source.source_type === "csv" ? ".csv" : ".json"}
                className="hidden"
                onChange={handleFile}
              />
              <Button variant="outline" size="sm" disabled={busy} onClick={() => fileInputRef.current?.click()}>
                <Upload className="h-3.5 w-3.5" />
                העלאת קובץ
              </Button>
            </>
          )}
          {(source.source_type === "api_generic" || source.source_type === "demo") && (
            <Button variant="outline" size="sm" disabled={busy} onClick={handleSync}>
              <RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />
              סנכרון עכשיו
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function NewSourceForm({ organizationId, onCreated }: { organizationId: string; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState<SourceConnection["source_type"]>("csv");
  const [endpoint, setEndpoint] = useState("");
  const [authType, setAuthType] = useState("none");
  const [authValue, setAuthValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      const config: Record<string, unknown> =
        sourceType === "api_generic" ? { endpoint, auth_type: authType, auth_value: authValue || undefined } : {};
      await api.createSource({ organization_id: organizationId, name, source_type: sourceType, config });
      onCreated();
    } catch {
      setError("יצירת המקור נכשלה. בדקו את הפרטים ונסו שוב.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-bold text-[var(--foreground)]">מקור נתונים חדש</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--muted-foreground)]">שם המקור</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="לדוגמה: ייבוא ספק X" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--muted-foreground)]">סוג מקור</label>
            <Select value={sourceType} onChange={(e) => setSourceType(e.target.value as SourceConnection["source_type"])}>
              <option value="csv">קובץ CSV</option>
              <option value="json">קובץ JSON</option>
              <option value="api_generic">API חיצוני (Adapter גנרי)</option>
            </Select>
          </div>
        </div>

        {sourceType === "api_generic" && (
          <div className="grid gap-3 rounded-md bg-[var(--muted)] p-3 sm:grid-cols-3">
            <div className="sm:col-span-3">
              <label className="mb-1 block text-xs font-medium text-[var(--muted-foreground)]">כתובת API</label>
              <Input value={endpoint} onChange={(e) => setEndpoint(e.target.value)} placeholder="https://provider.example.com/api/items" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--muted-foreground)]">שיטת הזדהות</label>
              <Select value={authType} onChange={(e) => setAuthType(e.target.value)}>
                <option value="none">ללא</option>
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
              </Select>
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-medium text-[var(--muted-foreground)]">מפתח/טוקן</label>
              <Input value={authValue} onChange={(e) => setAuthValue(e.target.value)} placeholder="יוזן כשיתחבר ספק אמיתי" />
            </div>
          </div>
        )}

        {error && <p className="text-sm text-[var(--danger-fg)]">{error}</p>}

        <Button onClick={submit} disabled={saving || !name}>
          {saving ? "יוצר…" : "יצירת מקור"}
        </Button>
      </CardContent>
    </Card>
  );
}
