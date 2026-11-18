import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { isPublicRoute } from "@/lib/auth/public-routes";

function requestFor(path: string): NextRequest {
  return new NextRequest(new URL(path, "http://zeph.test"));
}

describe("isPublicRoute", () => {
  it.each([
    "/",
    "/how-it-works",
    "/sign-in",
    "/sign-in/factor-one",
    "/sign-up",
    "/terms",
    "/privacy",
  ])("lets signed-out people open %s", (path) => {
    expect(isPublicRoute(requestFor(path))).toBe(true);
  });

  it.each([
    "/memories",
    "/check-ins",
    "/account",
    "/connect-telegram",
    "/onboarding",
    "/admin",
    "/admin/users",
    "/how-it-works-secret",
  ])("keeps %s behind sign-in", (path) => {
    expect(isPublicRoute(requestFor(path))).toBe(false);
  });
});
