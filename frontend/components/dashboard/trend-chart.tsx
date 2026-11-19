"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TrendPoint } from "@/lib/api";

const SERIES: { key: keyof TrendPoint; label: string; color: string }[] = [
  { key: "positive", label: "חיובי", color: "var(--sentiment-positive)" },
  { key: "neutral", label: "ניטרלי", color: "var(--sentiment-neutral)" },
  { key: "mixed", label: "מעורב", color: "var(--sentiment-mixed)" },
  { key: "negative", label: "שלילי", color: "var(--sentiment-negative)" },
];

function formatDate(value: string) {
  const d = new Date(value);
  return d.toLocaleDateString("he-IL", { day: "2-digit", month: "2-digit" });
}

export function TrendChart({ points }: { points: TrendPoint[] }) {
  if (!points.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-[var(--muted-foreground)]">
        אין נתוני מגמה להצגה בתקופה הנבחרת
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <defs>
          {SERIES.map((s) => (
            <linearGradient key={s.key} id={`fill-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={s.color} stopOpacity={0.5} />
              <stop offset="95%" stopColor={s.color} stopOpacity={0.05} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="bucket"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          labelFormatter={(v) => formatDate(String(v))}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            direction: "rtl",
          }}
        />
        <Legend
          formatter={(value) => SERIES.find((s) => s.key === value)?.label ?? value}
          wrapperStyle={{ fontSize: 12, direction: "rtl" }}
        />
        {SERIES.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            stackId="sentiment"
            stroke={s.color}
            fill={`url(#fill-${s.key})`}
            strokeWidth={1.5}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
