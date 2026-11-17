"use client";

import { SidebarAdminBadge } from "@/components/SidebarAdminBadge";
import { useMe } from "@/lib/queries";

/**
 * Who is signed in, at the foot of the sidebar: their initial, name and
 * email from `/me`. A User with no name is shown by their email. Grey bars
 * stand in while `/me` loads.
 *
 * @returns The signed-in User's name and email.
 */
export function SidebarAccount() {
  const me = useMe().data;
  if (!me) {
    return (
      <div className="flex items-center gap-2.5 p-2">
        <span className="sr-only">Loading your account</span>
        <span
          aria-hidden="true"
          className="size-8 flex-none rounded-full bg-line"
        />
        <span aria-hidden="true" className="flex flex-col gap-1.5">
          <span className="h-3 w-20 rounded bg-line" />
          <span className="h-3 w-32 rounded bg-line" />
        </span>
      </div>
    );
  }
  const email = me.email ?? "";
  const name = me.name || email;
  return (
    <div className="flex items-center gap-2.5 p-2">
      <span
        aria-hidden="true"
        className="flex size-8 flex-none items-center justify-center rounded-full bg-blue text-caption font-semibold text-white"
      >
        {name.charAt(0).toUpperCase()}
      </span>
      <span className="flex min-w-0 flex-col text-caption leading-[1.3]">
        <span className="flex items-center gap-1.5 font-semibold">
          {name}
          <SidebarAdminBadge />
        </span>
        <span className="overflow-hidden text-ellipsis text-ink-muted">
          {email}
        </span>
      </span>
    </div>
  );
}
