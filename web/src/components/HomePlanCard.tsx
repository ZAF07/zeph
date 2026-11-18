import Link from "next/link";

import { secondaryButton } from "@/components/button-styles";
import { HomeCard } from "@/components/HomeCard";
import { ToBuildTag } from "@/components/ToBuildTag";

/**
 * The Dashboard home card for the User's Plan. Plans have no backend yet,
 * so it shows the design's placeholders as they are, with the "To build"
 * tag.
 *
 * @returns The card.
 */
export function HomePlanCard() {
  return (
    <HomeCard
      headingId="home-plan-heading"
      title={
        <>
          Plan
          <ToBuildTag />
        </>
      }
      caption="Renews on [RENEWAL DATE]."
      basis="wide"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="text-[22px] font-normal text-cream">
            [PLAN NAME]
          </span>
          <span className="text-[13px] text-soft"> · [PRICE] /month</span>
        </div>
        <Link href="/plan" className={secondaryButton}>
          Manage plan
        </Link>
      </div>
    </HomeCard>
  );
}
