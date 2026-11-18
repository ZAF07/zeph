import { SectionIntro } from "@/components/SectionIntro";
import { siteBackgrounds } from "@/components/site-backgrounds";
import { siteColumn } from "@/components/site-styles";

/**
 * The questions and answers. Answers in square brackets are the design's
 * placeholders, kept as written.
 */
const questions = [
  {
    question: "What is Zeph?",
    answer:
      "Zeph is an AI companion you talk to on Telegram. It draws on philosophy, psychology and mindfulness to help you reflect, question your assumptions and decide what matters to you.",
  },
  {
    question: "How is this different from a regular AI chat?",
    answer:
      "Zeph remembers what you have told it, with your permission, and it can reach out first at times you choose. It is built to ask good questions, and it will disagree with you when that is more useful than agreeing.",
  },
  {
    question: "Will Zeph proactively check in with me?",
    answer:
      "Only if you turn check-ins on. You pick the times and how often in your dashboard, and you can switch them off at any time.",
  },
  {
    question: "Is my data private and secure?",
    answer:
      "You decide what Zeph remembers, and you can read, remove or export it from your dashboard. [YOUR DATA HANDLING DETAILS]",
  },
  {
    question: "Can I cancel my subscription anytime?",
    answer: "[YOUR CANCELLATION POLICY]",
  },
];

/**
 * Landing's FAQ section over the doorway picture: the intro and the
 * questions, each opening to show its answer.
 *
 * @returns The section.
 */
export function LandingFaq() {
  return (
    <div className={siteBackgrounds.landingFaq}>
      <section
        id="faq"
        className={`${siteColumn} flex flex-wrap items-start justify-end gap-x-[72px] gap-y-9 pt-[72px] pb-[380px] max-[899px]:pt-14 max-[899px]:pb-[350px]`}
      >
        <SectionIntro
          eyebrow="FAQ"
          title="Common questions."
          body="Everything you need to know about Zeph."
          className="max-w-[320px] min-w-0 flex-[1_1_260px]"
        />
        <div className="max-w-[440px] min-w-0 flex-[1_1_380px] border-t border-line">
          {questions.map((item) => (
            <details key={item.question} className="border-b border-line">
              <summary className="flex min-h-[52px] cursor-pointer list-none items-center justify-between gap-4 text-[15px] font-normal text-text [&::-webkit-details-marker]:hidden">
                {item.question}
                <span
                  aria-hidden="true"
                  className="text-[20px] font-light text-soft"
                >
                  +
                </span>
              </summary>
              <p className="mt-0 mb-[18px] max-w-[520px] text-[14px] text-soft">
                {item.answer}
              </p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
