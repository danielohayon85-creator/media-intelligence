import { ThemeToggle } from "@/components/theme-toggle";

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--card)] px-6 py-4">
      <div>
        <h1 className="text-lg font-bold">{title}</h1>
        {subtitle && <p className="text-sm text-[var(--muted-foreground)]">{subtitle}</p>}
      </div>
      <ThemeToggle />
    </header>
  );
}
