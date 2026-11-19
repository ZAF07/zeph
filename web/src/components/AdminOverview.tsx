import Link from "next/link";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CardFooterLink } from "@/components/CardFooterLink";
import { cardLink, filledPill, outlinedPill } from "@/components/card-styles";
import { CardRow } from "@/components/CardRow";
import { DetailRow } from "@/components/DetailRow";
import { HomeCard } from "@/components/HomeCard";
import { MessagesChart } from "@/components/MessagesChart";
import { OverviewCountTile } from "@/components/OverviewCountTile";
import { ToBuildTag } from "@/components/ToBuildTag";
import type { OverviewSample } from "@/lib/design-fixtures/overview";

/**
 * The admin Overview: counts, what needs attention, which Features are on,
 * messages over the last week and a Knowledge summary, each linking to its
 * admin page. Its counts have no backend yet, so it is labelled "Sample
 * data" and makes no backend calls.
 *
 * @param props - `overview` is what the page shows.
 * @returns The page.
 */
export function AdminOverview({ overview }: { overview: OverviewSample }) {
  return (
    <>
      <AdminPageHeader
        title={
          <>
            Overview
            <ToBuildTag />
          </>
        }
        lead="Counts only. Message text is never shown in the admin area."
        aside={
          <span className="rounded-pill border border-line-strong px-3 py-1 text-[12px] text-soft">
            Sample data
          </span>
        }
      />
      <div className="flex flex-wrap gap-5">
        {overview.counts.map((count) => (
          <OverviewCountTile key={count.label} count={count} />
        ))}
      </div>
      <div className="flex flex-wrap items-start gap-6">
        <HomeCard
          headingId="overview-attention-heading"
          title="Needs attention"
          caption="Things that are blocked or over a limit right now."
          basis="main"
        >
          {overview.needsAttention.map((item) => (
            <CardRow key={item.text}>
              <span className="inline-flex items-center gap-2.5 text-[14px] text-text">
                <span
                  aria-hidden="true"
                  className="size-2 flex-none rounded-full bg-orange"
                />
                {item.text}
              </span>
              <Link href={item.href} className={cardLink}>
                {item.linkLabel}
              </Link>
            </CardRow>
          ))}
        </HomeCard>
        <HomeCard
          headingId="overview-features-heading"
          title="Features"
          caption="Extras switched on for everyone."
          basis="side"
        >
          {overview.features.map((feature) => (
            <DetailRow key={feature.name} label={feature.name}>
              <span className={feature.isOn ? filledPill : outlinedPill}>
                {feature.isOn ? "On" : "Off"}
              </span>
            </DetailRow>
          ))}
          <CardFooterLink href="/admin/features" label="Open Features" />
        </HomeCard>
      </div>
      <div className="flex flex-wrap items-start gap-6">
        <HomeCard
          headingId="overview-messages-heading"
          title="Messages, last 7 days"
          aside={
            <Link href="/admin/usage" className={cardLink}>
              Open Usage
            </Link>
          }
          caption="All users, per day."
          basis="main"
        >
          <MessagesChart days={overview.messagesByDay} />
        </HomeCard>
        <HomeCard
          headingId="overview-knowledge-heading"
          title="Knowledge"
          caption="The material Zeph draws on."
          basis="side"
        >
          {overview.knowledge.map((line) => (
            <DetailRow key={line.label} label={line.label}>
              {line.value}
            </DetailRow>
          ))}
          <CardFooterLink href="/admin/knowledge" label="Open Knowledge" />
        </HomeCard>
      </div>
    </>
  );
}
