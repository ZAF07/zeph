/**
 * The Admin-worded note saying User Memory is off and why. Text between
 * double asterisks is shown in bold.
 *
 * @param props - `note` is the note the backend sent; "" while User Memory
 *   is on, which shows nothing.
 * @returns The note, or nothing.
 */
export function MemoryNote({ note }: { note: string }) {
  if (!note) {
    return null;
  }
  return (
    <p
      role="status"
      className="m-0 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
    >
      {note
        .split("**")
        .map((part, index) =>
          index % 2 === 1 ? <strong key={index}>{part}</strong> : part,
        )}
    </p>
  );
}
