/**
 * The bar of onboarding steps, filled up to the current one.
 *
 * @param props - `labels` names each step; `currentStep` is the zero-based
 *   step on screen.
 * @returns The progress bar.
 */
export function OnboardingProgress({
  labels,
  currentStep,
}: {
  labels: string[];
  currentStep: number;
}) {
  return (
    <nav aria-label="Onboarding progress" className="flex flex-col gap-2">
      <ol
        className="m-0 grid list-none gap-2 p-0"
        style={{
          gridTemplateColumns: `repeat(${labels.length}, minmax(0, 1fr))`,
        }}
      >
        {labels.map((label, index) => {
          const isCurrent = index === currentStep;
          return (
            <li
              key={label}
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
                {label}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="m-0 text-[12px] text-soft">
        Step {currentStep + 1} of {labels.length}
      </p>
    </nav>
  );
}
