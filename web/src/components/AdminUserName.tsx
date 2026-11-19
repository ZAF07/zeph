import type { AdminUser } from "@/lib/api-client";

/**
 * A User's name in the admin Users table, with their email under it when
 * they have a name.
 *
 * @param props - `user` is the User.
 * @returns The name and email.
 */
export function AdminUserName({ user }: { user: AdminUser }) {
  return (
    <>
      <div className="text-[14px] font-normal text-text">
        {user.name ?? user.email ?? "—"}
      </div>
      {user.name ? (
        <div className="text-[12px] [overflow-wrap:break-word] text-soft">
          {user.email}
        </div>
      ) : null}
    </>
  );
}
