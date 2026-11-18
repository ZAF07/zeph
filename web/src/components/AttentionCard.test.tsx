import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AttentionCard } from "@/components/AttentionCard";
import { PillLink } from "@/components/PillLink";

describe("AttentionCard", () => {
  it("says what is wrong and offers the way forward", () => {
    render(
      <AttentionCard
        title="Zeph can’t reach you yet."
        body="Conversations and check-ins happen in Telegram."
        action={
          <PillLink href="/connect-telegram" label="Connect Telegram" primary />
        }
      />,
    );

    expect(screen.getByText("Zeph can’t reach you yet.")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Connect Telegram" }),
    ).toBeInTheDocument();
  });
});
