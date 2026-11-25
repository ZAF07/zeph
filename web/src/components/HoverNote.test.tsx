import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HoverNote } from "@/components/HoverNote";

describe("HoverNote", () => {
  it("gives the control its note, for the pop-up and for screen readers", () => {
    render(
      <HoverNote noteId="locked-note" note="Locked for now.">
        <button aria-describedby="locked-note">Change</button>
      </HoverNote>,
    );

    expect(screen.getByRole("tooltip")).toHaveTextContent("Locked for now.");
    expect(
      screen.getByRole("button", { name: "Change" }),
    ).toHaveAccessibleDescription("Locked for now.");
  });

  it("shows the control alone when there is no note", () => {
    render(
      <HoverNote noteId="locked-note" note={null}>
        <button>Change</button>
      </HoverNote>,
    );

    expect(screen.getByRole("button", { name: "Change" })).toBeVisible();
    expect(screen.queryByRole("tooltip")).toBeNull();
  });
});
