import { SectionIntro } from "@/components/SectionIntro";
import { siteColumn, siteTag } from "@/components/site-styles";

/**
 * The moments on the day's timeline, in order. `dotColor` and `tagColor` are the
 * dot's background and the tag's text colour, which the design draws in
 * colours that are not tokens.
 */
const moments = [
  {
    tag: "Check-ins",
    dotColor: "bg-[#F0B49A]",
    tagColor: "text-[#F0B49A]",
    title: "It reaches out first, gently.",
    text: "Opt-in messages at times you choose. A question for the morning, never a streak to protect.",
  },
  {
    tag: "Applied wisdom",
    dotColor: "bg-[#EBD08A]",
    tagColor: "text-[#EBD08A]",
    title: "Old ideas, when they are useful.",
    text: "Eastern and Western philosophy, psychology and mindfulness, offered in plain words at the moment they apply.",
  },
  {
    tag: "Reflection",
    dotColor: "bg-[#E3A3BA]",
    tagColor: "text-[#E3A3BA]",
    title: "A place to think out loud.",
    text: "Talk through the day. Zeph asks, listens and disagrees when it should. It will not flatter you.",
  },
  {
    tag: "Memory",
    dotColor: "bg-[#B4BCF2]",
    tagColor: "text-[#B4BCF2]",
    title: "It remembers, with permission.",
    text: "What you care about carries into tomorrow's conversation. You can read every memory and remove any of them.",
  },
];

/**
 * Landing's "A day with Zeph" section: the intro and a timeline of the
 * moments Zeph is there for.
 *
 * @returns The section.
 */
export function LandingDay() {
  return (
    <section id="day" className={`${siteColumn} pt-14 pb-[72px]`}>
      <SectionIntro
        eyebrow="A day with Zeph"
        title={
          <>
            A thoughtful presence
            <br />
            throughout your day.
          </>
        }
        body="Not just when you ask, but when it matters. Zeph chooses the moment to reach out, and stays quiet when you need space."
        className="max-w-[340px] pb-12"
      />
      <div className="mx-auto box-content flex max-w-[560px] flex-col pl-1.5">
        {moments.map((moment, index) => (
          <div key={moment.tag} className="flex gap-x-7">
            <div
              className={`relative min-w-0 flex-1 border-l border-line pl-8 ${index === moments.length - 1 ? "pb-0" : "pb-12"}`}
            >
              <span
                aria-hidden="true"
                className={`absolute top-[7px] -left-1.5 size-[11px] rounded-full ${moment.dotColor}`}
              />
              <div className={`inline-block ${siteTag} ${moment.tagColor}`}>
                {moment.tag}
              </div>
              <h3 className="mt-3 mb-2 text-[24px] leading-[1.2] font-normal text-cream">
                {moment.title}
              </h3>
              <p className="m-0 text-soft">{moment.text}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
