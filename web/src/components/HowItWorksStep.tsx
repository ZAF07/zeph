/** One step on the How It Works page. */
export type HowItWorksStepDetails = {
  title: string;
  tag: string;
  text: string;
};

/**
 * One numbered step on How It Works: the round number with the line down
 * to the next step, the title with its tag, and the text.
 *
 * @param props - `number` is the step's number, `step` its words and
 *   `last` leaves off the line and the space below.
 * @returns The list item.
 */
export function HowItWorksStep({
  number,
  step,
  last,
}: {
  number: number;
  step: HowItWorksStepDetails;
  last: boolean;
}) {
  return (
    <li className="flex gap-x-6">
      <div className="flex flex-none flex-col items-center">
        <span className="box-border flex size-10 flex-none items-center justify-center rounded-full border border-line-strong text-[15px] font-normal text-cream">
          {number}
        </span>
        {last ? null : (
          <span aria-hidden="true" className="w-px flex-1 bg-line" />
        )}
      </div>
      <div className={`min-w-0 flex-1 ${last ? "pb-0" : "pb-11"}`}>
        <div className="flex min-h-10 flex-wrap items-center gap-x-[14px] gap-y-1.5">
          <h3 className="m-0 text-[22px] leading-[1.2] font-normal text-cream">
            {step.title}
          </h3>
          <span className="rounded-[6px] bg-white/7 px-2.5 py-0.5 text-[12px] font-normal text-soft">
            {step.tag}
          </span>
        </div>
        <p className="mt-2 mb-0 max-w-[560px] text-soft">{step.text}</p>
      </div>
    </li>
  );
}
