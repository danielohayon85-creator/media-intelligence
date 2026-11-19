"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radio } from "lucide-react";

import { NAV_ITEMS } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-l border-[var(--border)] bg-[var(--card)] lg:flex">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)]">
          <Radio className="h-4 w-4" />
        </div>
        <div>
          <div className="text-sm font-bold leading-tight">Media Intelligence</div>
          <div className="text-xs text-[var(--muted-foreground)]">מודיעין תקשורתי</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const isActive = item.available && pathname === item.href;
          const content = (
            <span
              className={cn(
                "flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive && "bg-[var(--primary)] text-[var(--primary-foreground)]",
                !isActive && item.available && "hover:bg-[var(--muted)]",
                !item.available && "text-[var(--muted-foreground)] opacity-60 cursor-not-allowed"
              )}
            >
              <span className="flex items-center gap-2">
                <item.icon className="h-4 w-4" />
                {item.label}
              </span>
              {!item.available && (
                <span className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-[10px] text-[var(--muted-foreground)]">
                  בקרוב
                </span>
              )}
            </span>
          );

          return item.available ? (
            <Link key={item.label} href={item.href}>
              {content}
            </Link>
          ) : (
            <div key={item.label}>{content}</div>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] px-4 py-3 text-xs text-[var(--muted-foreground)]">
        שלב א&apos; (MVP) · גרסה 0.1
      </div>
    </aside>
  );
}
