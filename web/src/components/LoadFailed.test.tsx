import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoadFailed } from "@/components/LoadFailed";

describe("LoadFailed", () => {
  it("says what failed and calls its handler on Try again", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(
      <LoadFailed
        title="Couldn’t load your memories"
        body="Check your connection and try again. Nothing has been lost."
        onRetry={onRetry}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load your memories",
    );
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
