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
    <nav aria-label="Onboarding progress" className="flex flex-col gap-2.5">
      <ol
        className="m-0 grid list-none gap-1.5 p-0"
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
              className="flex min-w-0 flex-col gap-2"
            >
              <span
                aria-hidden="true"
                className={`block h-1 rounded-full ${
                  index <= currentStep ? "bg-blue" : "bg-line"
                }`}
              />
              <span
                className={`overflow-hidden text-ellipsis whitespace-nowrap text-xs ${
                  isCurrent ? "font-semibold text-ink" : "text-ink-muted"
                }`}
              >
                {label}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="m-0 text-caption text-ink-muted">
        Step {currentStep + 1} of {labels.length}
      </p>
    </nav>
  );
}
