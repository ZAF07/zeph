import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fakeEnv = vi.hoisted(() => ({ designFixtures: false }));

vi.mock("@/env", () => ({ env: fakeEnv }));

vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("NEXT_NOT_FOUND");
  },
}));

const { default: StatesPreviewPage } =
  await import("@/app/design-preview/states/page");

describe("StatesPreviewPage", () => {
  beforeEach(() => {
    fakeEnv.designFixtures = false;
  });

  it("is not found outside design-fixture mode", () => {
    expect(() => StatesPreviewPage()).toThrow("NEXT_NOT_FOUND");
  });

  it("renders the States sheet in design-fixture mode", () => {
    fakeEnv.designFixtures = true;

    render(StatesPreviewPage());

    expect(
      screen.getByRole("heading", { level: 1, name: "States" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("alertdialog", { name: "Delete all memories?" }),
    ).toBeInTheDocument();
  });
});
