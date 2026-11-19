import { SectionIntro } from "@/components/SectionIntro";
import { siteColumn, siteTag } from "@/components/site-styles";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The moments on the day's timeline, in order. `slotPrefix` starts the keys of
 * the moment's tag, title and text in the Copy. `dotColor` and `tagColor`
 * are the dot's background and the tag's text colour, which the design
 * draws in colours that are not tokens.
 */
const moments = [
  {
    slotPrefix: "landing.day.check_ins",
    dotColor: "bg-[#F0B49A]",
    tagColor: "text-[#F0B49A]",
  },
  {
    slotPrefix: "landing.day.applied_wisdom",
    dotColor: "bg-[#EBD08A]",
    tagColor: "text-[#EBD08A]",
  },
  {
    slotPrefix: "landing.day.reflection",
    dotColor: "bg-[#E3A3BA]",
    tagColor: "text-[#E3A3BA]",
  },
  {
    slotPrefix: "landing.day.memory",
    dotColor: "bg-[#B4BCF2]",
    tagColor: "text-[#B4BCF2]",
  },
];

/**
 * Landing's "A day with Zeph" section: the intro and a timeline of the
 * moments Zeph is there for.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The section.
 */
export function LandingDay({ copy }: { copy: Copy }) {
  return (
    <section id="day" className={`${siteColumn} pt-14 pb-[72px]`}>
      <SectionIntro
        eyebrow={readCopy(copy, "landing.day.eyebrow")}
        title={
          <>
            {readCopy(copy, "landing.day.heading_first_line")}
            <br />
            {readCopy(copy, "landing.day.heading_second_line")}
          </>
        }
        body={readCopy(copy, "landing.day.lead")}
        className="max-w-[340px] pb-12"
      />
      <div className="mx-auto box-content flex max-w-[560px] flex-col pl-1.5">
        {moments.map((moment, index) => (
          <div key={moment.slotPrefix} className="flex gap-x-7">
            <div
              className={`relative min-w-0 flex-1 border-l border-line pl-8 ${index === moments.length - 1 ? "pb-0" : "pb-12"}`}
            >
              <span
                aria-hidden="true"
                className={`absolute top-[7px] -left-1.5 size-[11px] rounded-full ${moment.dotColor}`}
              />
              <div className={`inline-block ${siteTag} ${moment.tagColor}`}>
                {readCopy(copy, `${moment.slotPrefix}.tag`)}
              </div>
              <h3 className="mt-3 mb-2 text-[24px] leading-[1.2] font-normal text-cream">
                {readCopy(copy, `${moment.slotPrefix}.title`)}
              </h3>
              <p className="m-0 text-soft">
                {readCopy(copy, `${moment.slotPrefix}.text`)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
