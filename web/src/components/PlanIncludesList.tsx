/**
 * What a plan includes, one ticked line each, as Landing's pricing and the
 * Plan page draw it. It grows to fill its card so the buttons below line up.
 *
 * @param props - `includes` are the lines, in order.
 * @returns The list.
 */
export function PlanIncludesList({ includes }: { includes: string[] }) {
  return (
    <ul className="mt-1.5 mb-[14px] flex flex-1 list-none flex-col gap-2 p-0">
      {includes.map((line, index) => (
        <li key={index} className="flex gap-2.5 text-[14px] text-soft">
          <svg
            aria-hidden="true"
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mt-1 flex-none"
          >
            <path d="M2 7.5l3.2 3.2L12 3.800" />
          </svg>
          <span>{line}</span>
        </li>
      ))}
    </ul>
  );
}
