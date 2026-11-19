"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AdminUserName } from "@/components/AdminUserName";
import { rowActionButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { RolePill } from "@/components/RolePill";
import { SearchField } from "@/components/SearchField";
import { TableCards, type TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import { TableNoMatches } from "@/components/TableNoMatches";
import { ToBuildTag } from "@/components/ToBuildTag";
import { UserManagePanel } from "@/components/UserManagePanel";
import type { AdminUser } from "@/lib/api-client";
import { formatDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const headCell =
  "py-2.5 pr-3 pl-0 text-left text-[11px] font-medium tracking-[1.5px] whitespace-nowrap text-soft uppercase";

const bodyCell = "py-3 pr-3 pl-0 text-[14px] text-soft";

/**
 * Counts a thing in plain words, e.g. "1 admin" or "2 admins".
 *
 * @param count - How many there are.
 * @param word - The thing being counted, singular.
 * @returns The count with the word.
 */
function countOf(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

/**
 * Tells whether a User matches the search text.
 *
 * @param user - The User.
 * @param search - What was typed into the search box.
 * @returns True if the User should be listed.
 */
function matchesSearch(user: AdminUser, search: string): boolean {
  const needle = search.trim().toLowerCase();
  return [user.name, user.email].some((text) =>
    (text ?? "").toLowerCase().includes(needle),
  );
}

/**
 * Says whether a User has connected Telegram.
 *
 * @param user - The User.
 * @returns "Connected" or "Not connected".
 */
function telegramText(user: AdminUser): string {
  return user.telegram_connected ? "Connected" : "Not connected";
}

/**
 * The admin Users page: everyone with an account, with counts but never
 * message text. Manage opens a User in the side panel, to change their role
 * and Features.
 *
 * @returns The search, totals and table, or a loading, no-match, empty or
 *   error state, and the side panel once a User is chosen.
 */
export function AdminUsers() {
  const apiClient = useApiClient();
  const [search, setSearch] = useState("");
  const [managedUserId, setManagedUserId] = useState<string | null>(null);

  const usersQuery = useQuery({
    queryKey: queryKeys.adminUsers,
    queryFn: () => apiClient.listAdminUsers(),
  });
  const users = usersQuery.data;
  const shown = users?.filter((user) => matchesSearch(user, search)) ?? [];
  const managedUser = users?.find((user) => user.id === managedUserId);

  const manageButton = (user: AdminUser) => (
    <button
      type="button"
      onClick={() => setManagedUserId(user.id)}
      className={rowActionButton}
    >
      Manage
    </button>
  );

  const cardColumns: TableColumn<AdminUser>[] = [
    { heading: "User", cell: (user) => <AdminUserName user={user} /> },
    { heading: "Role", cell: (user) => <RolePill role={user.role} /> },
    { heading: "Signed up", cell: (user) => formatDay(user.signed_up_at) },
    { heading: "Telegram", cell: telegramText },
    { heading: "Conversations", cell: (user) => user.conversation_count },
    { heading: "Messages", cell: (user) => user.messages_sent },
    { heading: "Plan", cell: () => "[PLAN]" },
    { heading: "Actions", cell: manageButton },
  ];

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <SearchField
          label="Search by name or email"
          placeholder="Search users"
          value={search}
          onChange={setSearch}
          labelShown
        />
        {users ? (
          <span className="self-end pb-3 text-[13px] text-soft">
            {countOf(users.length, "user")} ·{" "}
            {countOf(
              users.filter((user) => user.role === "admin").length,
              "admin",
            )}
          </span>
        ) : null}
      </div>

      {usersQuery.isPending ? <TableLoading label="Loading users" /> : null}

      {!users && usersQuery.isError ? (
        <LoadFailed
          title="Couldn’t load users"
          body="The user list didn’t respond. No roles were changed."
          onRetry={() => void usersQuery.refetch()}
        />
      ) : null}

      {users && users.length === 0 ? (
        <TableEmpty
          title="No users yet"
          body="People appear here after they sign up. You’ll see sign-up date, Telegram status and counts — never message text."
        />
      ) : null}

      {users && users.length > 0 && shown.length === 0 ? (
        <TableNoMatches />
      ) : null}

      {shown.length > 0 ? (
        <div className="flex flex-wrap items-start gap-6">
          <section className="box-border min-w-0 flex-[999_1_560px] rounded-card border border-line bg-panel px-6 py-[22px]">
            <h2 className="m-0 flex items-center text-[17px] font-normal text-cream">
              All users
            </h2>
            <div className="mt-4">
              <div className="overflow-x-auto max-[899px]:hidden">
                <table className="w-full min-w-[720px] border-collapse">
                  <thead>
                    <tr>
                      {[
                        "User",
                        "Role",
                        "Signed up",
                        "Telegram",
                        "Conversations",
                        "Messages",
                      ].map((heading) => (
                        <th key={heading} scope="col" className={headCell}>
                          {heading}
                        </th>
                      ))}
                      <th scope="col" className={headCell}>
                        Plan
                        <ToBuildTag />
                      </th>
                      <th scope="col">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.map((user) => {
                      const isManaged = user.id === managedUserId;
                      return (
                        <tr
                          key={user.id}
                          className={`border-t border-line ${
                            isManaged ? "bg-[rgba(255,255,255,.04)]" : ""
                          }`}
                        >
                          <td
                            className={`py-3 pr-3 ${isManaged ? "pl-3" : "pl-0"}`}
                          >
                            <AdminUserName user={user} />
                          </td>
                          <td className={bodyCell}>
                            <RolePill role={user.role} />
                          </td>
                          <td className={bodyCell}>
                            {formatDay(user.signed_up_at)}
                          </td>
                          <td className={bodyCell}>{telegramText(user)}</td>
                          <td className={bodyCell}>
                            {user.conversation_count}
                          </td>
                          <td className={bodyCell}>{user.messages_sent}</td>
                          <td className={bodyCell}>[PLAN]</td>
                          <td className="p-0">{manageButton(user)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <TableCards
                columns={cardColumns}
                rows={shown}
                rowKey={(user) => user.id}
              />
            </div>
          </section>
          {managedUser ? (
            <UserManagePanel key={managedUser.id} user={managedUser} />
          ) : null}
        </div>
      ) : null}
    </>
  );
}
