/**
 * The bar of onboarding steps, filled up to the current one.
 *
 * @param props - `label` names the bar for screen readers; `labels` names
 *   each step; `currentStep` is the zero-based step on screen; `stepCount`
 *   is the line under the bar, like "Step 2 of 6".
 * @returns The progress bar.
 */
export function OnboardingProgress({
  label,
  labels,
  currentStep,
  stepCount,
}: {
  label: string;
  labels: string[];
  currentStep: number;
  stepCount: string;
}) {
  return (
    <nav aria-label={label} className="flex flex-col gap-2">
      <ol
        className="m-0 grid list-none gap-2 p-0"
        style={{
          gridTemplateColumns: `repeat(${labels.length}, minmax(0, 1fr))`,
        }}
      >
        {labels.map((stepLabel, index) => {
          const isCurrent = index === currentStep;
          return (
            <li
              key={index}
              aria-current={isCurrent ? "step" : undefined}
              className="flex flex-col gap-1.5"
            >
              <span
                aria-hidden="true"
                className={`h-[3px] rounded-[2px] ${
                  index <= currentStep ? "bg-cream" : "bg-line"
                }`}
              />
              <span
                className={`overflow-hidden text-ellipsis whitespace-nowrap text-[12px] ${
                  isCurrent ? "font-normal text-text" : "font-light text-soft"
                }`}
              >
                {stepLabel}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="m-0 text-[12px] text-soft">{stepCount}</p>
    </nav>
  );
}
