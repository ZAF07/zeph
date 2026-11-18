import { afterEach, describe, expect, it, vi } from "vitest";

import { chooseApiClient } from "@/lib/choose-api-client";

const apiUrl = "http://api.test";
const getToken = async () => "token-1";

describe("chooseApiClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("signs in as Alex on design fixtures, without calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const client = chooseApiClient(
      { apiUrl, designFixtures: true },
      getToken,
      "",
    );
    const me = await client.getMe();

    expect(me).toMatchObject({
      name: "Alex",
      email: "alex@example.com",
      role: "user",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("signs in as Zaf the Admin when the zeph-design-as=admin cookie is set", async () => {
    const client = chooseApiClient(
      { apiUrl, designFixtures: true },
      getToken,
      "theme=dark; zeph-design-as=admin",
    );

    expect(await client.getMe()).toMatchObject({ name: "Zaf", role: "admin" });
  });

  it("gives the shell the AI notice drawn in the sidebar", async () => {
    const client = chooseApiClient(
      { apiUrl, designFixtures: true },
      getToken,
      "",
    );

    expect(await client.getPlatformContent()).toMatchObject({
      ai_notice_short: "Zeph is an AI, not a therapist or crisis service.",
    });
  });

  it("fails a call that has no fixture yet, naming it", async () => {
    const client = chooseApiClient(
      { apiUrl, designFixtures: true },
      getToken,
      "",
    );

    await expect(client.listAdminUsers()).rejects.toThrow(
      "No design fixture for listAdminUsers yet",
    );
  });

  it("uses the real backend when fixture mode is off, even with the cookie", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ name: "Maya" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = chooseApiClient(
      { apiUrl, designFixtures: false },
      getToken,
      "zeph-design-as=admin",
    );

    expect(await client.getMe()).toEqual({ name: "Maya" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/me",
      expect.objectContaining({
        headers: { Authorization: "Bearer token-1" },
      }),
    );
  });
});
