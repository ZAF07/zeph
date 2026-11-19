import type { MessagesDay } from "@/lib/design-fixtures/overview";

/**
 * The admin Overview's bar chart of messages a day: one bar per day, its
 * height a share of the chart, with the day's name under it.
 *
 * @param props - `days` are the bars, oldest first.
 * @returns The chart.
 */
export function MessagesChart({ days }: { days: MessagesDay[] }) {
  return (
    <div className="flex h-[150px] items-end gap-2.5">
      {days.map((day) => (
        <div
          key={day.day}
          className="flex h-full flex-1 flex-col items-center justify-end gap-2"
        >
          <span
            aria-hidden="true"
            className="w-full max-w-10 rounded-t-[6px] bg-zeph"
            style={{ height: `${day.heightPercent}%` }}
          />
          <span className="text-[12px] text-soft">{day.day}</span>
        </div>
      ))}
    </div>
  );
}
