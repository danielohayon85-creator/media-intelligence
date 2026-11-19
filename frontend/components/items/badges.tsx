import { Badge, type BadgeProps } from "@/components/ui/badge";
import type { AnalysisResult, MediaItem } from "@/lib/api";

const SENTIMENT_LABEL: Record<AnalysisResult["sentiment"], string> = {
  positive: "חיובי",
  negative: "שלילי",
  neutral: "ניטרלי",
  mixed: "מעורב",
};

const SENTIMENT_VARIANT: Record<AnalysisResult["sentiment"], BadgeProps["variant"]> = {
  positive: "success",
  negative: "danger",
  neutral: "secondary",
  mixed: "warning",
};

export function SentimentBadge({ sentiment }: { sentiment: AnalysisResult["sentiment"] }) {
  return <Badge variant={SENTIMENT_VARIANT[sentiment]}>{SENTIMENT_LABEL[sentiment]}</Badge>;
}

const RELEVANCE_LABEL: Record<AnalysisResult["relevance"], string> = {
  direct: "רלוונטיות ישירה",
  indirect: "רלוונטיות עקיפה",
  background: "מידע רקע",
  not_relevant: "לא רלוונטי",
};

export function RelevanceBadge({ relevance }: { relevance: AnalysisResult["relevance"] }) {
  return <Badge variant="outline">{RELEVANCE_LABEL[relevance]}</Badge>;
}

const DEDUP_LABEL: Record<MediaItem["dedup_role"], string> = {
  original: "כתבה מקורית",
  duplicate: "כפילות",
  reprint: "ציטוט חוזר",
  follow_up: "המשך סיפור",
};

export function DedupBadge({ role }: { role: MediaItem["dedup_role"] }) {
  if (role === "original") return null;
  return <Badge variant="secondary">{DEDUP_LABEL[role]}</Badge>;
}

export const MEDIA_TYPE_LABEL: Record<string, string> = {
  online: "אונליין",
  print: "עיתונות מודפסת",
  tv: "טלוויזיה",
  radio: "רדיו",
  social: "רשתות חברתיות",
};

export const COVERAGE_STYLE_LABEL: Record<string, string> = {
  factual: "עובדתי / דיווחי",
  critical: "ביקורתי",
  supportive: "תומך",
  interpretive: "פרשני",
  investigative: "תחקירי",
  polemic: "פולמוסי",
  sensational: "סנסציוני",
};

export const FRAMING_LABEL: Record<string, string> = {
  organizational_success: "הצלחה ארגונית",
  organizational_failure: "כשל ארגוני",
  routine_activity: "פעילות שוטפת",
  confrontation: "עימות בין גורמים",
  legal_issue: "סוגיה משפטית",
  public_interest: "אינטרס ציבורי",
};
