import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OnboardingStepFrame } from "@/components/OnboardingStepFrame";

const words = { wordmark: "Zeph", homeLinkLabel: "Zeph home" };

describe("OnboardingStepFrame", () => {
  it("shows the Zeph wordmark linking home above the step", () => {
    render(<OnboardingStepFrame {...words}>Step body</OnboardingStepFrame>);

    const home = screen.getByRole("link", { name: "Zeph home" });
    expect(home).toHaveTextContent("Zeph");
    expect(home).toHaveAttribute("href", "/");
    expect(screen.getByText("Step body")).toBeInTheDocument();
  });

  it("draws the dashed line only when asked", () => {
    const { container, rerender } = render(
      <OnboardingStepFrame {...words}>Step body</OnboardingStepFrame>,
    );
    expect(container.querySelector("section")).not.toHaveClass("border-dashed");

    rerender(
      <OnboardingStepFrame {...words} hasSeparator>
        Step body
      </OnboardingStepFrame>,
    );
    expect(container.querySelector("section")).toHaveClass("border-dashed");
  });
});
