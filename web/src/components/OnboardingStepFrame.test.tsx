import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OnboardingStepFrame } from "@/components/OnboardingStepFrame";

describe("OnboardingStepFrame", () => {
  it("shows the Zeph wordmark linking home above the step", () => {
    render(<OnboardingStepFrame>Step body</OnboardingStepFrame>);

    expect(screen.getByRole("link", { name: "Zeph home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByText("Step body")).toBeInTheDocument();
  });

  it("draws the dashed line only when asked", () => {
    const { container, rerender } = render(
      <OnboardingStepFrame>Step body</OnboardingStepFrame>,
    );
    expect(container.querySelector("section")).not.toHaveClass("border-dashed");

    rerender(<OnboardingStepFrame hasSeparator>Step body</OnboardingStepFrame>);
    expect(container.querySelector("section")).toHaveClass("border-dashed");
  });
});
