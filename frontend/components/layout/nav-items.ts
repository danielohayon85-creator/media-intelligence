import {
  LayoutDashboard,
  Newspaper,
  Radar,
  Share2,
  Tv,
  AlertTriangle,
  Lightbulb,
  Megaphone,
  FileBarChart,
  MessageSquareText,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  available: boolean;
}

// לפי תפריט הניווט המלא במפרט (סעיף 15); הפריטים המסומנים available=false
// שייכים לשלב ב'/ג' ומוצגים כ"בקרוב" כדי לשקף את מפת הדרכים המלאה של המוצר.
export const NAV_ITEMS: NavItem[] = [
  { label: "תמונת מצב", href: "/", icon: LayoutDashboard, available: true },
  { label: "תובנות AI", href: "/insights", icon: Lightbulb, available: true },
  { label: "מגמות", href: "/", icon: Radar, available: false },
  { label: "נרטיבים", href: "/", icon: Share2, available: false },
  { label: "סיקור ופרסומים", href: "/items", icon: Newspaper, available: true },
  { label: "כלי תקשורת וכתבים", href: "/", icon: Tv, available: false },
  { label: "סיכונים והתרעות", href: "/", icon: AlertTriangle, available: false },
  { label: "הזדמנויות תקשורתיות", href: "/", icon: Lightbulb, available: false },
  { label: "אפקטיביות דוברות", href: "/", icon: Megaphone, available: false },
  { label: "דוחות", href: "/", icon: FileBarChart, available: false },
  { label: "שאל את המידע", href: "/", icon: MessageSquareText, available: false },
  { label: "הגדרות וחיבורי API", href: "/sources", icon: Settings, available: true },
];
