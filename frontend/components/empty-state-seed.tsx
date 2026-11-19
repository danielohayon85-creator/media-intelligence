"use client";

import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useOrg } from "@/lib/org-context";

export function EmptyStateSeed() {
  const { seedDemo, seeding, error } = useOrg();

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--muted)]">
        <Sparkles className="h-6 w-6 text-[var(--muted-foreground)]" />
      </div>
      <div>
        <h2 className="text-lg font-bold">אין עדיין נתונים במערכת</h2>
        <p className="mt-1 max-w-md text-sm text-[var(--muted-foreground)]">
          חברו מקור נתונים (CSV, JSON או API) במסך ההגדרות, או טענו נתוני הדגמה סינתטיים
          כדי לראות את הדשבורד בפעולה.
        </p>
      </div>
      {error && <p className="text-sm text-[var(--danger-fg)]">{error}</p>}
      <Button onClick={() => seedDemo()} disabled={seeding}>
        {seeding ? "טוען נתוני הדגמה…" : "טען נתוני הדגמה"}
      </Button>
    </div>
  );
}
