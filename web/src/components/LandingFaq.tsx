import { SectionIntro } from "@/components/SectionIntro";
import { siteBackgrounds } from "@/components/site-backgrounds";
import { siteColumn } from "@/components/site-styles";
import { type Copy, readCopy } from "@/lib/copy";

/** How many questions the FAQ has; each has a question and an answer slot. */
const questionNumbers = [1, 2, 3, 4, 5];

/**
 * Landing's FAQ section over the doorway picture: the intro and the
 * questions, each opening to show its answer.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The section.
 */
export function LandingFaq({ copy }: { copy: Copy }) {
  return (
    <div className={siteBackgrounds.landingFaq}>
      <section
        id="faq"
        className={`${siteColumn} flex flex-wrap items-start justify-end gap-x-[72px] gap-y-9 pt-[72px] pb-[380px] max-[899px]:pt-14 max-[899px]:pb-[350px]`}
      >
        <SectionIntro
          eyebrow={readCopy(copy, "landing.faq.eyebrow")}
          title={readCopy(copy, "landing.faq.heading")}
          body={readCopy(copy, "landing.faq.lead")}
          className="max-w-[320px] min-w-0 flex-[1_1_260px]"
        />
        <div className="max-w-[440px] min-w-0 flex-[1_1_380px] border-t border-line">
          {questionNumbers.map((number) => (
            <details key={number} className="border-b border-line">
              <summary className="flex min-h-[52px] cursor-pointer list-none items-center justify-between gap-4 text-[15px] font-normal text-text [&::-webkit-details-marker]:hidden">
                {readCopy(copy, `landing.faq.question_${number}`)}
                <span
                  aria-hidden="true"
                  className="text-[20px] font-light text-soft"
                >
                  +
                </span>
              </summary>
              <p className="mt-0 mb-[18px] max-w-[520px] text-[14px] text-soft">
                {readCopy(copy, `landing.faq.answer_${number}`)}
              </p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
