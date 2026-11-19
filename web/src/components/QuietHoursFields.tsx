/** A time field, drawn like the design's quiet hours boxes. */
const timeField =
  "box-border min-h-[46px] w-full rounded-input border border-line-strong bg-bg-deep px-3.5 text-[15px] text-text [color-scheme:dark] disabled:cursor-not-allowed";

/**
 * The "From" and "Until" times of a User's quiet hours, in their local time.
 *
 * @param props - `labels` are the group's screen-reader name and the two
 *   fields' words; `start` and `end` are times like "22:00", `disabled` stops
 *   changes, and `onStartChange` and `onEndChange` get a new full time.
 * @returns The two time fields side by side.
 */
export function QuietHoursFields({
  labels,
  start,
  end,
  disabled = false,
  onStartChange,
  onEndChange,
}: {
  labels: { group: string; from: string; until: string };
  start: string;
  end: string;
  disabled?: boolean;
  onStartChange: (start: string) => void;
  onEndChange: (end: string) => void;
}) {
  return (
    <div
      role="group"
      aria-label={labels.group}
      className="flex w-full flex-wrap gap-3"
    >
      <label className="flex flex-[1_1_120px] flex-col gap-1.5">
        <span className="text-[13px] text-soft">{labels.from}</span>
        <input
          className={timeField}
          type="time"
          required
          disabled={disabled}
          value={start}
          onChange={(event) => {
            if (event.target.value) {
              onStartChange(event.target.value);
            }
          }}
        />
      </label>
      <label className="flex flex-[1_1_120px] flex-col gap-1.5">
        <span className="text-[13px] text-soft">{labels.until}</span>
        <input
          className={timeField}
          type="time"
          required
          disabled={disabled}
          value={end}
          onChange={(event) => {
            if (event.target.value) {
              onEndChange(event.target.value);
            }
          }}
        />
      </label>
    </div>
  );
}
