"use client";

import { Select } from "@/components/ui/select";

export const DATE_RANGE_PRESETS = [
  { label: "7 ימים אחרונים", days: 7 },
  { label: "30 ימים אחרונים", days: 30 },
  { label: "90 ימים אחרונים", days: 90 },
];

export function dateRangeFromDays(days: number): { dateFrom: string; dateTo: string } {
  const dateTo = new Date();
  const dateFrom = new Date(dateTo);
  dateFrom.setDate(dateFrom.getDate() - days);
  return { dateFrom: dateFrom.toISOString(), dateTo: dateTo.toISOString() };
}

export function DateRangeSelect({
  days,
  onChange,
}: {
  days: number;
  onChange: (days: number) => void;
}) {
  return (
    <Select value={days} onChange={(e) => onChange(Number(e.target.value))} aria-label="בחירת תקופה">
      {DATE_RANGE_PRESETS.map((preset) => (
        <option key={preset.days} value={preset.days}>
          {preset.label}
        </option>
      ))}
    </Select>
  );
}
