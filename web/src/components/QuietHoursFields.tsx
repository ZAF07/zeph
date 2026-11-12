import { fieldLabel, inputField } from "@/components/form-styles";

/**
 * The "From" and "Until" times of a User's quiet hours, in their local time.
 *
 * @param props - `start` and `end` are times like "22:00", `disabled` stops
 *   changes, and `onStartChange` and `onEndChange` get a new full time.
 * @returns The two time fields side by side.
 */
export function QuietHoursFields({
  start,
  end,
  disabled = false,
  onStartChange,
  onEndChange,
}: {
  start: string;
  end: string;
  disabled?: boolean;
  onStartChange: (start: string) => void;
  onEndChange: (end: string) => void;
}) {
  return (
    <div role="group" aria-label="Quiet hours" className="flex flex-wrap gap-3">
      <label className={`${fieldLabel} flex-[1_1_120px]`}>
        From
        <input
          className={inputField}
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
      <label className={`${fieldLabel} flex-[1_1_120px]`}>
        Until
        <input
          className={inputField}
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
