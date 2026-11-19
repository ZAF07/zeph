import Link from "next/link";

import { secondaryButton } from "@/components/button-styles";
import { HomeCard } from "@/components/HomeCard";
import { ToBuildTag } from "@/components/ToBuildTag";
import { readCopy, type Copy } from "@/lib/copy";

/**
 * The Dashboard home card for the User's Plan. Plans have no backend yet,
 * so it shows the design's placeholders as they are, with the "To build"
 * tag.
 *
 * @param props - `copy` is Home's Copy.
 * @returns The card.
 */
export function HomePlanCard({ copy }: { copy: Copy }) {
  const text = (key: string) => readCopy(copy, `home.plan.${key}`);
  return (
    <HomeCard
      headingId="home-plan-heading"
      title={
        <>
          {text("title")}
          <ToBuildTag />
        </>
      }
      caption={text("caption")}
      basis="wide"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="text-[22px] font-normal text-cream">
            {text("name")}
          </span>
          <span className="text-[13px] text-soft"> {text("price")}</span>
        </div>
        <Link href="/plan" className={secondaryButton}>
          {text("manage_button")}
        </Link>
      </div>
    </HomeCard>
  );
}
