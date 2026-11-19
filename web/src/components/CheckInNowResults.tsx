import { rowActionButton } from "@/components/button-styles";
import type { CheckInNowResultForUser } from "@/lib/api-client";
import { checkInNowResultLabels } from "@/lib/check-in-schedule";

/**
 * Says what happened to a Check in Now for each User asked for: requested,
 * or refused and why.
 *
 * @param props - `results` is each User's result, in the order asked;
 *   `names` says what to call each User, by User ID; `onDismiss` hides the
 *   results.
 * @returns The results, with a way to hide them.
 */
export function CheckInNowResults({
  results,
  names,
  onDismiss,
}: {
  results: CheckInNowResultForUser[];
  names: Record<string, string>;
  onDismiss: () => void;
}) {
  const requested = results.filter((item) => item.result === "requested");
  return (
    <div
      role="status"
      className="flex flex-col gap-2 rounded-card border border-line bg-panel px-[18px] py-4 text-[14px] text-text"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-cream">
          Check in now: {requested.length} of {results.length} requested
        </span>
        <button type="button" className={rowActionButton} onClick={onDismiss}>
          Dismiss
        </button>
      </div>
      <ul className="m-0 flex list-none flex-col gap-1 p-0">
        {results.map((item) => (
          <li key={item.user_id}>
            <span className="text-cream">
              {names[item.user_id] ?? item.user_id}
            </span>
            : {checkInNowResultLabels[item.result]}
          </li>
        ))}
      </ul>
    </div>
  );
}
