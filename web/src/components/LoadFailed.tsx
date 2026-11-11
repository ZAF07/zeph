import { secondaryButton } from "@/components/button-styles";

/**
 * The block shown when a page's data could not be loaded, with Try again.
 *
 * @param props - `title` says what failed, `body` reassures what still
 *   holds, and `onRetry` loads again.
 * @returns The error block.
 */
export function LoadFailed({
  title,
  body,
  onRetry,
}: {
  title: string;
  body: string;
  onRetry: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-2.5 rounded-card border border-danger-line bg-danger-tint p-8"
    >
      <h2 className="m-0 text-[17px] font-semibold text-danger-deep">
        {title}
      </h2>
      <p className="m-0 text-[15px] text-ink-soft">{body}</p>
      <button
        type="button"
        className={`${secondaryButton} bg-white`}
        onClick={onRetry}
      >
        Try again
      </button>
    </div>
  );
}
