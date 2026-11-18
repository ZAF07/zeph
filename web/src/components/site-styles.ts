/**
 * The page width and side gutter every block of the public pages shares:
 * 1160px wide, 32px gutters, 20px below 900px.
 */
export const siteColumn =
  "mx-auto box-border max-w-[1160px] px-8 max-[899px]:px-5";

/**
 * A two-column section of the public pages: the intro on the left and the
 * content on the right, wrapping to one column when there is no room.
 */
export const splitSection = "flex flex-wrap items-start gap-x-14 gap-y-9";

/** The intro column of a `splitSection`. */
export const splitIntro = "max-w-[340px] min-w-0 flex-[1_1_280px]";

/** The content column of a `splitSection`. */
export const splitContent = "min-w-0 flex-[999_1_560px]";

/** The small rounded tag beside a timeline moment or a step title. */
export const siteTag =
  "rounded-[6px] bg-white/7 px-2.5 py-0.5 text-[12px] font-normal";
