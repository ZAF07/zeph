import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { secondaryButton } from "@/components/button-styles";
import { PausedNotice } from "@/components/PausedNotice";

describe("PausedNotice", () => {
  it("says what is off and turns it back on", async () => {
    const user = userEvent.setup();
    const onResume = vi.fn();
    render(
      <PausedNotice
        title="Check-ins are paused until 25 Nov"
        body="Zeph won’t message first until then."
        action={
          <button type="button" className={secondaryButton} onClick={onResume}>
            Resume now
          </button>
        }
      />,
    );

    expect(
      screen.getByText("Check-ins are paused until 25 Nov"),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Resume now" }));

    expect(onResume).toHaveBeenCalledTimes(1);
  });
});
