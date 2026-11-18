import { LandingChatBubble } from "@/components/LandingChatBubble";
import { SectionIntro } from "@/components/SectionIntro";
import { siteColumn } from "@/components/site-links";

/** The sample conversation, in order. `pause` draws the three dots. */
const conversation: (
  { from: "zeph" | "person"; text: string } | { from: "pause" }
)[] = [
  {
    from: "zeph",
    text: "You've been pushing hard lately. How are you actually feeling beneath the momentum?",
  },
  {
    from: "person",
    text: "Honestly? Tired. But I'm also afraid to slow down. It feels like I'll fall behind if I do.",
  },
  {
    from: "zeph",
    text: "That's a familiar pattern: equating rest with losing ground. What do you think you're really afraid of if you take a proper break?",
  },
  {
    from: "person",
    text: "Maybe that I'm not as capable as I think. That the progress will stop, and I'll be left with the same old doubts again.",
  },
  {
    from: "zeph",
    text: "That's a useful insight. It sounds less about productivity and more about self-trust. What would it look like to rest as part of your progress, and not as a pause from it?",
  },
  { from: "pause" },
  {
    from: "person",
    text: "I'm thinking of a bigger change, maybe moving to a van and travelling for a while. It feels exciting, but also a bit reckless. Am I just escaping from something?",
  },
  {
    from: "zeph",
    text: "It could be both: an escape and a deliberate step toward a life that feels more like you. Let's unpack it. What are you hoping to find on the road, and what are you hoping to leave behind?",
  },
  { from: "pause" },
];

/**
 * Landing's "Conversations with Zeph" section: the intro and a sample
 * conversation.
 *
 * @returns The section.
 */
export function LandingConversation() {
  return (
    <section
      id="conversations"
      className={`${siteColumn} flex flex-wrap items-start gap-x-14 gap-y-9 pt-14 pb-[72px]`}
    >
      <SectionIntro
        eyebrow="Conversations with Zeph"
        title={
          <>
            Real conversations
            <br />
            for real growth.
          </>
        }
        body="See how Zeph thinks, responds, and helps you go deeper."
        className="max-w-[340px] min-w-0 flex-[1_1_280px]"
      />
      <div className="min-w-0 flex-[999_1_560px]">
        <div className="flex flex-col gap-4">
          {conversation.map((message, index) =>
            message.from === "pause" ? (
              <div
                key={index}
                aria-hidden="true"
                className="flex justify-center gap-[5px] py-1"
              >
                <span className="size-1 rounded-full bg-soft" />
                <span className="size-1 rounded-full bg-soft" />
                <span className="size-1 rounded-full bg-soft" />
              </div>
            ) : (
              <LandingChatBubble
                key={index}
                from={message.from}
                text={message.text}
              />
            ),
          )}
        </div>
      </div>
    </section>
  );
}
