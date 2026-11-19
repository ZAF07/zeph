import {
  type ChatSender,
  LandingChatBubble,
} from "@/components/LandingChatBubble";
import { SectionIntro } from "@/components/SectionIntro";
import {
  siteColumn,
  splitContent,
  splitIntro,
  splitSection,
} from "@/components/site-styles";
import { type Copy, readCopy } from "@/lib/copy";

/**
 * The sample conversation, in order: who sends each message and the Copy
 * slot holding its words. `pause` draws the three dots.
 */
const conversation: ({ from: ChatSender; slot: string } | { from: "pause" })[] =
  [
    { from: "zeph", slot: "landing.conversations.message_1" },
    { from: "person", slot: "landing.conversations.message_2" },
    { from: "zeph", slot: "landing.conversations.message_3" },
    { from: "person", slot: "landing.conversations.message_4" },
    { from: "zeph", slot: "landing.conversations.message_5" },
    { from: "pause" },
    { from: "person", slot: "landing.conversations.message_6" },
    { from: "zeph", slot: "landing.conversations.message_7" },
    { from: "pause" },
  ];

/**
 * Landing's "Conversations with Zeph" section: the intro and a sample
 * conversation.
 *
 * @param props - `copy` is the website's Copy.
 * @returns The section.
 */
export function LandingConversation({ copy }: { copy: Copy }) {
  return (
    <section
      id="conversations"
      className={`${siteColumn} ${splitSection} pt-14 pb-[72px]`}
    >
      <SectionIntro
        eyebrow={readCopy(copy, "landing.conversations.eyebrow")}
        title={
          <>
            {readCopy(copy, "landing.conversations.heading_first_line")}
            <br />
            {readCopy(copy, "landing.conversations.heading_second_line")}
          </>
        }
        body={readCopy(copy, "landing.conversations.lead")}
        className={splitIntro}
      />
      <div className={splitContent}>
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
                text={readCopy(copy, message.slot)}
              />
            ),
          )}
        </div>
      </div>
    </section>
  );
}
