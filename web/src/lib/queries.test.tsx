import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ApiClient } from "@/lib/api-client";
import { useMe, useUpdatePreferences } from "@/lib/queries";
import { renderWithQueries } from "@/test/render-with-queries";
import { userWithRole } from "@/test/fixtures";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function NameShown({ label }: { label: string }) {
  const me = useMe();
  return (
    <p>
      {label}: {me.data?.name ?? "loading"}
    </p>
  );
}

function RenameButton() {
  const updatePreferences = useUpdatePreferences();
  return (
    <button
      type="button"
      onClick={() => updatePreferences.mutate({ name: "Mei" })}
    >
      Rename
    </button>
  );
}

describe("useMe", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("loads the User once however many components show them", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(
      <>
        <NameShown label="Sidebar" />
        <NameShown label="Gate" />
        <NameShown label="Page" />
      </>,
    );

    expect(await screen.findByText("Page: Maya")).toBeInTheDocument();
    expect(screen.getByText("Sidebar: Maya")).toBeInTheDocument();
    expect(apiClient.getMe).toHaveBeenCalledTimes(1);
  });

  it("shows a saved change in every component without loading again", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));
    apiClient.updatePreferences.mockResolvedValue({
      ...userWithRole("user"),
      name: "Mei",
    });
    const user = userEvent.setup();
    renderWithQueries(
      <>
        <NameShown label="Sidebar" />
        <NameShown label="Page" />
        <RenameButton />
      </>,
    );
    await screen.findByText("Page: Maya");

    await user.click(screen.getByRole("button", { name: "Rename" }));

    expect(await screen.findByText("Sidebar: Mei")).toBeInTheDocument();
    expect(screen.getByText("Page: Mei")).toBeInTheDocument();
    expect(apiClient.getMe).toHaveBeenCalledTimes(1);
  });
});
