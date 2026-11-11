"use client";

import { useCallback, useEffect, useState } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import { ApiError, type AdminUser, type UserRole } from "@/lib/api-client";
import { formatDay } from "@/lib/dates";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; users: AdminUser[] };

type Filter = "all" | "admins" | "telegram_not_connected";

type Flash = { text: string; isError: boolean };

const filters: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "admins", label: "Admins" },
  { id: "telegram_not_connected", label: "Telegram not connected" },
];

const pill =
  "inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium";

/**
 * Counts a thing in plain words, e.g. "1 Admin" or "2 Admins".
 *
 * @param count - How many there are.
 * @param word - The thing being counted, singular.
 * @returns The count with the word.
 */
function countOf(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

/**
 * Tells whether a User matches the search text and the chosen filter.
 *
 * @param user - The User.
 * @param search - What was typed into the search box.
 * @param filter - The chosen filter.
 * @returns True if the User should be listed.
 */
function isShown(user: AdminUser, search: string, filter: Filter): boolean {
  const needle = search.trim().toLowerCase();
  const matchesSearch =
    needle === "" ||
    [user.name, user.email].some((text) =>
      (text ?? "").toLowerCase().includes(needle),
    );
  const matchesFilter =
    filter === "all" ||
    (filter === "admins" && user.role === "admin") ||
    (filter === "telegram_not_connected" && !user.telegram_connected);
  return matchesSearch && matchesFilter;
}

/**
 * The admin Users page: everyone with an account, with counts but never
 * message text, and buttons to make or remove Admins.
 *
 * @returns The search, filters and table, or a loading, empty or error state.
 */
export function AdminUsers() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [flash, setFlash] = useState<Flash | null>(null);
  const [changingUserId, setChangingUserId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "loaded", users: await apiClient.listAdminUsers() });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  async function changeRole(target: AdminUser, role: UserRole) {
    const displayName = target.name ?? target.email ?? "This User";
    setChangingUserId(target.id);
    setFlash(null);
    try {
      const change = await apiClient.changeUserRole(target.id, role);
      setState((current) =>
        current.kind === "loaded"
          ? {
              kind: "loaded",
              users: current.users.map((user) =>
                user.id === change.id ? { ...user, role: change.role } : user,
              ),
            }
          : current,
      );
      setFlash({
        text:
          change.role === "admin"
            ? `${displayName} is now an Admin.`
            : `${displayName} is no longer an Admin.`,
        isError: false,
      });
    } catch (error) {
      const isLastAdmin = error instanceof ApiError && error.status === 409;
      setFlash({
        text: isLastAdmin
          ? `Can’t remove ${displayName}: they’re the only Admin. Make someone else an Admin first, so the platform is never left without one.`
          : `Couldn’t change ${displayName}’s role. Please try again.`,
        isError: true,
      });
    } finally {
      setChangingUserId(null);
    }
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <label className="flex-[1_1_280px]">
          <span className="sr-only">Search users</span>
          <input
            className={inputField}
            type="search"
            placeholder="Search by name or email"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <div
          role="group"
          aria-label="Filter"
          className="flex flex-wrap gap-1.5"
        >
          {filters.map((option) => (
            <button
              key={option.id}
              type="button"
              aria-pressed={filter === option.id}
              onClick={() => setFilter(option.id)}
              className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium ${
                filter === option.id
                  ? "border-ink bg-ink text-white"
                  : "border-line-strong bg-transparent text-ink-body"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {flash ? (
        <p
          role="status"
          className={`m-0 rounded-xl px-4 py-3.5 text-sm ${
            flash.isError
              ? "border border-danger-line bg-danger-tint text-danger-deep"
              : "bg-blue-tint text-blue-deep"
          }`}
        >
          {flash.text}
        </p>
      ) : null}

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading users"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="Couldn’t load users"
          body="The user list didn’t respond. No roles were changed."
          onRetry={() => void load()}
        />
      ) : null}

      {state.kind === "loaded" && state.users.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No users yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            People appear here after they sign up. You’ll see sign-up date,
            Telegram status and counts — never message text.
          </p>
        </div>
      ) : null}

      {state.kind === "loaded" && state.users.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border border-line bg-white">
            <table className="w-full min-w-[860px] border-collapse text-sm">
              <caption className="border-b border-line px-4 py-2.5 text-left">
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                  <LockIcon />
                  No message content ·{" "}
                  {countOf(
                    state.users.filter((user) => user.role === "admin").length,
                    "Admin",
                  )}{" "}
                  · {countOf(state.users.length, "User")}
                </span>
              </caption>
              <thead>
                <tr>
                  {[
                    "User",
                    "Signed up",
                    "Telegram",
                    "Conversations",
                    "Messages sent",
                    "Role",
                  ].map((heading) => (
                    <th
                      key={heading}
                      scope="col"
                      className={`whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted ${
                        heading === "Conversations" ||
                        heading === "Messages sent"
                          ? "text-right"
                          : "text-left"
                      }`}
                    >
                      {heading}
                    </th>
                  ))}
                  <th scope="col" className="border-b border-line bg-subtle">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {state.users
                  .filter((user) => isShown(user, search, filter))
                  .map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-line last:border-b-0"
                    >
                      <td className="px-[18px] py-3.5">
                        <span className="flex flex-col">
                          <span className="font-medium">
                            {user.name ?? user.email ?? "—"}
                          </span>
                          {user.name ? (
                            <span className="break-all text-caption text-ink-muted">
                              {user.email}
                            </span>
                          ) : null}
                        </span>
                      </td>
                      <td className="px-[18px] py-3.5">
                        {formatDay(user.signed_up_at)}
                      </td>
                      <td className="px-[18px] py-3.5">
                        <span
                          className={`${pill} ${
                            user.telegram_connected
                              ? "bg-blue-tint text-blue-deep"
                              : "bg-code text-ink-body"
                          }`}
                        >
                          {user.telegram_connected
                            ? "Connected"
                            : "Not connected"}
                        </span>
                      </td>
                      <td className="px-[18px] py-3.5 text-right tabular-nums">
                        {user.conversation_count}
                      </td>
                      <td className="px-[18px] py-3.5 text-right tabular-nums">
                        {user.messages_sent}
                      </td>
                      <td className="px-[18px] py-3.5">
                        <span
                          className={`${pill} ${
                            user.role === "admin"
                              ? "bg-ink text-white"
                              : "bg-code text-ink-body"
                          }`}
                        >
                          {user.role === "admin" ? "Admin" : "User"}
                        </span>
                      </td>
                      <td className="px-[18px] py-3.5 text-right">
                        <button
                          type="button"
                          disabled={changingUserId === user.id}
                          onClick={() =>
                            void changeRole(
                              user,
                              user.role === "admin" ? "user" : "admin",
                            )
                          }
                          className={compactSecondaryButton}
                        >
                          {user.role === "admin"
                            ? "Remove Admin"
                            : "Make Admin"}
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <p className="m-0 text-caption text-ink-muted">
            Admins can edit the Persona, prompts and platform settings. The last
            Admin can’t be demoted — promote someone else first.
          </p>
        </>
      ) : null}
    </>
  );
}
