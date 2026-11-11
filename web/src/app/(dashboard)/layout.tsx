import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { Sidebar } from "@/components/Sidebar";
import { getCurrentAccount } from "@/lib/auth/server";

/**
 * The Dashboard shell: sidebar beside the page.
 *
 * @param props - `children` is the page.
 * @returns The shell.
 */
export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const account = await getCurrentAccount();
  if (!account) {
    redirect("/sign-in");
  }
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <div className="md:w-[260px] md:flex-none">
        <Sidebar account={account} />
      </div>
      <main className="min-w-0 flex-1 px-4 py-12 md:px-12">
        <div className="mx-auto flex max-w-[880px] flex-col gap-8">
          {children}
        </div>
      </main>
    </div>
  );
}
