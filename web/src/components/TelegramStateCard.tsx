import type { ReactNode } from "react";

import { panelCard } from "@/components/card-styles";

/**
 * One of the Connect Telegram card's other states (waiting, connected,
 * expired, linked elsewhere), in the main card's box: a title, one line and
 * its buttons.
 *
 * @param props - `role` is "status" for news and "alert" for a problem;
 *   `title` and `body` are its words, with a coral title when `isProblem`;
 *   `actions` are its buttons.
 * @returns The card.
 */
export function TelegramStateCard({
  role,
  title,
  body,
  isProblem = false,
  actions,
}: {
  role: "status" | "alert";
  title: string;
  body: string;
  isProblem?: boolean;
  actions: ReactNode;
}) {
  return (
    <div role={role} className={panelCard}>
      <div
        className={`text-[15px] font-normal ${isProblem ? "text-danger" : "text-cream"}`}
      >
        {title}
      </div>
      <div className="mt-1.5 text-[13px] text-soft [overflow-wrap:anywhere]">
        {body}
      </div>
      <div className="mt-[18px] flex flex-wrap gap-2">{actions}</div>
    </div>
  );
}
