import type { CheckInKindSummary } from "@/lib/api-client";

/**
 * The read-only "What Zeph might reach out about" list: each Check-in Kind
 * that may be sent to the User, with its description.
 *
 * @param props - `kinds` are the Check-in Kinds, in order.
 * @returns The list, or nothing if there are no Kinds.
 */
export function CheckInKindsList({ kinds }: { kinds: CheckInKindSummary[] }) {
  if (kinds.length === 0) {
    return null;
  }
  return (
    <section
      aria-labelledby="check-in-kinds-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-6"
    >
      <h2 id="check-in-kinds-heading" className="m-0 text-[17px] font-semibold">
        What Zeph might reach out about
      </h2>
      <ul className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(min(260px,100%),1fr))] gap-x-6 gap-y-3 p-0">
        {kinds.map((kind) => (
          <li
            key={kind.name}
            className="flex flex-col gap-0.5 border-t border-line pt-3"
          >
            <span className="font-semibold">{kind.name}</span>
            <span className="text-caption text-ink-muted">
              {kind.description}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
