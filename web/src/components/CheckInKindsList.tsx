import type { CheckInKindSummary } from "@/lib/api-client";

/**
 * The read-only "What a check-in can be" list: each Check-in Kind that may
 * be sent to the User, with its description.
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
      className="flex flex-col gap-5 min-[900px]:gap-6"
    >
      <div>
        <h2
          id="check-in-kinds-heading"
          className="m-0 text-[20px] font-normal text-cream"
        >
          What a check-in can be
        </h2>
        <p className="mt-1.5 mb-0 max-w-[600px] text-[14px] text-soft">
          Zeph picks the kind that fits the moment.
        </p>
      </div>
      <ul className="m-0 flex list-none flex-wrap gap-4 p-0">
        {kinds.map((kind) => (
          <li
            key={kind.name}
            className="box-border min-w-0 flex-[1_1_260px] rounded-tile border border-line px-5 py-4"
          >
            <div className="text-[15px] font-normal text-text">{kind.name}</div>
            <div className="text-[13px] text-soft">{kind.description}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
