import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/headers", () => ({
  cookies: async () => ({ toString: () => "" }),
}));

const { loadCopy } = await import("@/lib/server-copy");

describe("loadCopy", () => {
  beforeEach(() => {
    vi.stubEnv("SERVER_API_URL", "http://backend.test");
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("reads the public Copy from the backend's server address, signed out", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({ texts: { "landing.faq.eyebrow": "FAQ" } }),
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    expect(await loadCopy()).toEqual({ "landing.faq.eyebrow": "FAQ" });
    expect(fetchMock).toHaveBeenCalledWith("http://backend.test/api/copy", {
      method: "GET",
      headers: {},
      body: undefined,
    });
  });

  it("gives null when the backend can't be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );

    expect(await loadCopy()).toBeNull();
  });
});
