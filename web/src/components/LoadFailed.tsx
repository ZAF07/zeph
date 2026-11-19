import { secondaryButton } from "@/components/button-styles";

/**
 * The block shown when a page or card could not load, with Try again.
 *
 * @param props - `title` says what failed, `body` reassures what still
 *   holds, `onRetry` loads again, and `retryLabel` is the button's words,
 *   which website pages take from Copy (admin pages keep "Try again").
 * @returns The error block.
 */
export function LoadFailed({
  title,
  body,
  onRetry,
  retryLabel = "Try again",
}: {
  title: string;
  body: string;
  onRetry: () => void;
  retryLabel?: string;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-2.5 rounded-card border border-danger px-[26px] py-6"
    >
      <h2 className="m-0 text-[17px] font-normal text-danger">{title}</h2>
      <p className="m-0 text-[14px] text-soft">{body}</p>
      <button type="button" className={secondaryButton} onClick={onRetry}>
        {retryLabel}
      </button>
    </div>
  );
}
