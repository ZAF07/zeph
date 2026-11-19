"use client";

import type { ReactNode } from "react";

import { readCopy, type Copy } from "@/lib/copy";
import { useMe } from "@/lib/queries";

/** Keeps a line of the row to one line, ending with an ellipsis if too long. */
const cutShort = "overflow-hidden text-ellipsis whitespace-nowrap";

/**
 * Who is signed in, in the sidebar and phone menu: a person icon, their name
 * and, below it, their email, or "Admin" for an Admin. A User with no name
 * is shown by their email. A name or email too long for the row is cut
 * short with an ellipsis and shown in full on hover. Placeholders stand in
 * while `/me` loads. "Admin" is an admin word, not Copy.
 *
 * @param props - `copy` is the menu's Copy; `action` sits at the end of the row, as Sign out does in the phone menu.
 * @returns The signed-in User's row.
 */
export function SidebarAccount({
  copy,
  action,
}: {
  copy: Copy;
  action?: ReactNode;
}) {
  const me = useMe().data;
  const name = me ? me.name || me.email : null;
  const detail = me?.role === "admin" ? "Admin" : (me?.email ?? null);
  const textWidth = action ? "min-w-0 flex-1" : "min-w-0";
  return (
    <div className="flex items-center gap-3 border-t border-line px-3.5 pt-3.5 pb-0">
      <span className="box-border flex size-9 flex-none items-center justify-center rounded-full border border-line-strong">
        <svg
          aria-hidden="true"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          className="text-soft"
        >
          <circle cx="8" cy="5.4" r="2.8" />
          <path d="M2.6 14c.6-3 2.7-4.4 5.4-4.4s4.800 1.400 5.4 4.4" />
        </svg>
      </span>
      {me ? (
        <div className={textWidth}>
          <div
            title={name ?? undefined}
            className={`text-[14px] font-normal text-text ${cutShort}`}
          >
            {name}
          </div>
          <div
            title={detail ?? undefined}
            className={`text-[12px] text-soft ${cutShort}`}
          >
            {detail}
          </div>
        </div>
      ) : (
        <div className={`${textWidth} flex flex-col gap-1.5`}>
          <span className="sr-only">
            {readCopy(copy, "shared.dashboard.loading_account")}
          </span>
          <span aria-hidden="true" className="h-3 w-20 rounded bg-line" />
          <span aria-hidden="true" className="h-3 w-32 rounded bg-line" />
        </div>
      )}
      {action}
    </div>
  );
}
