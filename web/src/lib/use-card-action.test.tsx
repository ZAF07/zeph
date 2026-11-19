import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api-client";
import { useCardAction } from "@/lib/use-card-action";

async function runFailing(failure: unknown) {
  const { result } = renderHook(() => useCardAction());
  await act(() =>
    result.current.run(() => Promise.reject(failure), "Couldn’t save."),
  );
  return result.current;
}

describe("useCardAction", () => {
  it("keeps the backend's reason for a refused change", async () => {
    expect(
      (await runFailing(new ApiError(422, "/x", "Name taken."))).failedMessage,
    ).toBe("Name taken.");
    expect(
      (await runFailing(new ApiError(409, "/x", "Still in use.")))
        .failedMessage,
    ).toBe("Still in use.");
  });

  it("uses its own words for any other failure", async () => {
    expect(
      (await runFailing(new ApiError(500, "/x", "Boom"))).failedMessage,
    ).toBe("Couldn’t save.");
    expect((await runFailing(new ApiError(422, "/x"))).failedMessage).toBe(
      "Couldn’t save.",
    );
    expect((await runFailing(new Error("down"))).failedMessage).toBe(
      "Couldn’t save.",
    );
  });

  it("is not busy and clears the failure after a success", async () => {
    const { result } = renderHook(() => useCardAction());
    await act(() => result.current.run(() => Promise.resolve(), "Failed."));
    expect(result.current.isBusy).toBe(false);
    expect(result.current.failedMessage).toBeNull();
  });
});
