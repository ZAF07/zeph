import Markdown from "react-markdown";

const previewStyles = [
  "text-[16px] text-text",
  "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
  "[&_h1]:mb-3 [&_h1]:mt-8 [&_h1]:text-[24px] [&_h1]:font-normal [&_h1]:text-cream",
  "[&_h2]:mb-2.5 [&_h2]:mt-7 [&_h2]:text-[20px] [&_h2]:font-normal [&_h2]:leading-tight [&_h2]:text-cream",
  "[&_h3]:mb-2 [&_h3]:mt-6 [&_h3]:text-[17px] [&_h3]:font-normal [&_h3]:text-cream",
  "[&_h4]:mb-2 [&_h4]:mt-5 [&_h4]:text-[15px] [&_h4]:font-normal [&_h4]:text-cream",
  "[&_p]:my-3",
  "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:my-1",
  "[&_blockquote]:my-4 [&_blockquote]:border-l-[3px] [&_blockquote]:border-line-strong [&_blockquote]:pl-4 [&_blockquote]:text-soft",
  "[&_code]:rounded-[6px] [&_code]:bg-bg-deep [&_code]:px-1 [&_code]:font-mono [&_code]:text-[0.9em]",
  "[&_pre]:my-4 [&_pre]:overflow-x-auto [&_pre]:rounded-input [&_pre]:bg-bg-deep [&_pre]:p-4",
  "[&_hr]:my-6 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-line",
  "[&_a]:underline",
  "break-words",
].join(" ");

/**
 * Shows Markdown as formatted text in Zeph's type styles. Raw HTML in the
 * text is left out, never run.
 *
 * @param props - `text` is the Markdown.
 * @returns The formatted text.
 */
export function MarkdownPreview({ text }: { text: string }) {
  return (
    <div className={previewStyles}>
      <Markdown skipHtml>{text}</Markdown>
    </div>
  );
}
