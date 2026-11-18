/**
 * One message in Landing's sample conversation: Zeph's on the left in a
 * filled bubble, the person's on the right in an outlined one, each beside
 * its round avatar.
 *
 * @param props - `from` says who sent it; `text` is the message.
 * @returns The message row.
 */
export function LandingChatBubble({
  from,
  text,
}: {
  from: "zeph" | "person";
  text: string;
}) {
  if (from === "zeph") {
    return (
      <div className="flex items-start gap-[14px]">
        <span className="flex size-10 flex-none items-center justify-center rounded-full bg-zeph">
          <svg
            aria-hidden="true"
            width="18"
            height="10"
            viewBox="0 0 18 10"
            fill="none"
            stroke="#F3E8D6"
            strokeWidth="1.8"
            strokeLinecap="round"
          >
            <path d="M1 6c2.5-5 5.5-5 8-1s5.5 4 8-1" />
          </svg>
        </span>
        <div className="box-content max-w-[440px] rounded-tile bg-zeph px-[18px] py-3 text-[14.5px] text-text">
          {text}
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start justify-end gap-[14px]">
      <div className="box-content max-w-[400px] rounded-tile border border-line-strong px-[18px] py-3 text-[14.5px] text-text">
        {text}
      </div>
      <span className="box-border flex size-10 flex-none items-center justify-center rounded-full border border-line-strong">
        <svg
          aria-hidden="true"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="#BDD0D5"
          strokeWidth="1.4"
          strokeLinecap="round"
        >
          <circle cx="8" cy="5.4" r="2.8" />
          <path d="M2.6 14c.6-3 2.7-4.4 5.4-4.4s4.800 1.400 5.4 4.4" />
        </svg>
      </span>
    </div>
  );
}
