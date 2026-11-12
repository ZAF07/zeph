import Markdown from "react-markdown";

const previewStyles = [
  "text-body text-ink-body",
  "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
  "[&_h1]:mb-3 [&_h1]:mt-8 [&_h1]:text-h2 [&_h1]:font-normal [&_h1]:text-ink",
  "[&_h2]:mb-2.5 [&_h2]:mt-7 [&_h2]:text-[22px] [&_h2]:font-medium [&_h2]:leading-tight [&_h2]:text-ink",
  "[&_h3]:mb-2 [&_h3]:mt-6 [&_h3]:text-h3 [&_h3]:font-semibold [&_h3]:text-ink",
  "[&_h4]:mb-2 [&_h4]:mt-5 [&_h4]:font-semibold [&_h4]:text-ink",
  "[&_p]:my-3",
  "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:my-1",
  "[&_blockquote]:my-4 [&_blockquote]:border-l-[3px] [&_blockquote]:border-line-strong [&_blockquote]:pl-4 [&_blockquote]:text-ink-soft",
  "[&_code]:rounded [&_code]:bg-code [&_code]:px-1 [&_code]:font-mono [&_code]:text-[0.9em]",
  "[&_pre]:my-4 [&_pre]:overflow-x-auto [&_pre]:rounded-input [&_pre]:bg-code [&_pre]:p-4",
  "[&_hr]:my-6 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-line",
  "[&_a]:underline",
  "break-words",
].join(" ");

/**
 * Shows Markdown as formatted text in Zeph's type styles. Raw HTML in the
 * text is shown as text, never run.
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
