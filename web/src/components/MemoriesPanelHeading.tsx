/**
 * The title and short explanation at the top of a Memories tab.
 *
 * @param props - `title` names the tab's contents and `body` explains them.
 * @returns The heading block.
 */
export function MemoriesPanelHeading({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div>
      <h2 className="m-0 text-[20px] font-normal text-cream">{title}</h2>
      <p className="mt-1.5 mb-0 max-w-[600px] text-[14px] text-soft">{body}</p>
    </div>
  );
}
