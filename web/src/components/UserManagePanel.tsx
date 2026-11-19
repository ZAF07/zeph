"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { UserFeatureSwitches } from "@/components/UserFeatureSwitches";
import { ApiError, type AdminUser, type UserRole } from "@/lib/api-client";
import { formatDay } from "@/lib/dates";
import { queryKeys, reloadUserPages } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type RoleNote = { text: string; isError: boolean };

const sectionHeading =
  "mt-[18px] mb-1 text-[13px] font-medium tracking-[1.5px] text-soft uppercase";

/**
 * The Users page's side panel for one User: their role and a button to
 * make or remove an Admin, their Features switches, what Zeph holds about
 * them (counts only), and a link to their Check-ins. Its heading takes focus
 * when it opens.
 *
 * @param props - `user` is the User being managed.
 * @returns The panel, named by the User's name.
 */
export function UserManagePanel({ user }: { user: AdminUser }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [roleNote, setRoleNote] = useState<RoleNote | null>(null);
  const displayName = user.name ?? user.email ?? "This User";

  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const changeRole = useMutation({
    mutationFn: (role: UserRole) => apiClient.changeUserRole(user.id, role),
    onMutate: () => setRoleNote(null),
    onSuccess: (change) => {
      queryClient.setQueryData<AdminUser[]>(queryKeys.adminUsers, (current) =>
        current?.map((listed) =>
          listed.id === change.id ? { ...listed, role: change.role } : listed,
        ),
      );
      reloadUserPages(queryClient);
      setRoleNote({
        text:
          change.role === "admin"
            ? `${displayName} is now an Admin.`
            : `${displayName} is no longer an Admin.`,
        isError: false,
      });
    },
    onError: (error) => {
      const isLastAdmin = error instanceof ApiError && error.status === 409;
      setRoleNote({
        text: isLastAdmin
          ? `Can’t remove ${displayName}: they’re the only Admin. Make someone else an Admin first, so the platform is never left without one.`
          : `Couldn’t change ${displayName}’s role. Please try again.`,
        isError: true,
      });
    },
  });

  const holds = [
    { label: "Life threads", value: String(user.life_thread_count) },
    { label: "Move outcomes", value: String(user.move_outcome_count) },
    { label: "Portrait", value: user.has_portrait ? "Written" : "Not written" },
  ];
  const scheduleSearch = new URLSearchParams({
    search: user.email ?? user.name ?? "",
  });

  return (
    <section
      aria-labelledby="managed-user-heading"
      className="box-border min-w-0 flex-[1_1_300px] rounded-card border border-line bg-panel px-6 py-[22px]"
    >
      <h2
        id="managed-user-heading"
        ref={headingRef}
        tabIndex={-1}
        className="m-0 flex items-center text-[17px] font-normal [overflow-wrap:anywhere] text-cream"
      >
        {displayName}
      </h2>
      <div className="mt-4">
        <div className="text-[12px] [overflow-wrap:anywhere] text-soft">
          {user.email ? `${user.email} · ` : ""}signed up{" "}
          {formatDay(user.signed_up_at)}
        </div>

        <h3 className={sectionHeading}>Role</h3>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-[14px] text-text">
            {user.role === "admin" ? "Admin" : "User"}
          </span>
          <button
            type="button"
            disabled={changeRole.isPending}
            onClick={() =>
              changeRole.mutate(user.role === "admin" ? "user" : "admin")
            }
            className={secondaryButton}
          >
            {user.role === "admin" ? "Remove admin" : "Make admin"}
          </button>
        </div>
        {roleNote ? (
          <div className="mt-2">
            {roleNote.isError ? (
              <SaveFailedNote>{roleNote.text}</SaveFailedNote>
            ) : (
              <SavedNote>{roleNote.text}</SavedNote>
            )}
          </div>
        ) : null}

        <h3 className={sectionHeading}>Features for this user</h3>
        <UserFeatureSwitches user={user} />

        <h3 className={sectionHeading}>What Zeph holds</h3>
        {holds.map((hold, index) => (
          <div
            key={hold.label}
            className={`box-content flex min-h-11 flex-wrap items-center justify-between gap-x-4 gap-y-1 ${
              index > 0 ? "border-t border-line" : ""
            }`}
          >
            <span className="text-[14px] text-soft">{hold.label}</span>
            <span className="text-[14px] text-text">{hold.value}</span>
          </div>
        ))}
        <div className="border-t border-line">
          <Link
            href={`/admin/check-in-schedule?${scheduleSearch.toString()}`}
            className="inline-flex min-h-11 items-center text-[13px] text-text"
          >
            Open this user in Check-in Schedule
          </Link>
        </div>
      </div>
    </section>
  );
}
