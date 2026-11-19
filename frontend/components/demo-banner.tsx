import { FlaskConical } from "lucide-react";

export function DemoBanner() {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-[var(--warning-fg)]/30 bg-[var(--warning-bg)] px-4 py-2 text-sm text-[var(--warning-fg)]">
      <FlaskConical className="h-4 w-4 shrink-0" />
      <span className="font-medium">נתוני הדגמה בלבד</span>
      <span className="text-[var(--warning-fg)]/80">
        — המערכת מציגה כרגע נתונים סינתטיים לצורך הדגמה. לאחר חיבור ספק ניטור אמיתי יוצגו נתוני אמת בלבד.
      </span>
    </div>
  );
}
