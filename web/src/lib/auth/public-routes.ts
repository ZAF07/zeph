import { createRouteMatcher } from "@clerk/nextjs/server";

/**
 * Tells the middleware which pages signed-out people may open: Landing,
 * How It Works and Pricing, sign-in and sign-up, and the legal pages.
 * Every other page needs sign-in.
 *
 * @param request - The incoming request.
 * @returns True when the page is public.
 */
export const isPublicRoute = createRouteMatcher([
  "/",
  "/how-it-works",
  "/pricing",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/terms",
  "/privacy",
]);
