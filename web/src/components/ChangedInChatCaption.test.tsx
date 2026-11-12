import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";

describe("ChangedInChatCaption", () => {
  it("says the setting was changed in chat, with the User's local day", () => {
    render(
      <ChangedInChatCaption
        changedAt="2026-11-02T18:30:00Z"
        timeZone="Asia/Singapore"
      />,
    );

    expect(screen.getByText("Changed in chat · 3 Nov")).toBeInTheDocument();
  });

  it("shows nothing for a setting not changed in chat", () => {
    const { container } = render(
      <ChangedInChatCaption changedAt={undefined} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
