import type { ModelCallContent } from "@/lib/api-client";

const label =
  "m-0 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted";
const textBlock =
  "m-0 max-h-[320px] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-code px-3.5 py-3 font-mono text-xs";

/**
 * What a model call was given and answered: instructions, history, tools
 * offered, tool calls with their results, the response and the model's
 * reasoning. Only ever shown for Admins' own chats and Evals.
 *
 * @param props - `content` is the call's kept content.
 * @returns The content, one section after another.
 */
export function ModelCallContentDetails({
  content,
}: {
  content: ModelCallContent;
}) {
  return (
    <div className="flex flex-col gap-4">
      <section className="flex flex-col gap-1.5">
        <h3 className={label}>Instructions</h3>
        <pre className={textBlock}>{content.instructions}</pre>
      </section>
      <section className="flex flex-col gap-1.5">
        <h3 className={label}>History</h3>
        <ol className="m-0 flex list-none flex-col gap-1.5 p-0">
          {content.history.map((line, index) => (
            <li key={index} className="flex flex-col gap-0.5">
              <span className="text-xs font-medium text-ink-muted">
                {line.role}
              </span>
              <pre className={textBlock}>{line.text}</pre>
            </li>
          ))}
        </ol>
      </section>
      {content.tools_offered.length > 0 ? (
        <section className="flex flex-col gap-1.5">
          <h3 className={label}>Tools offered</h3>
          <p className="m-0 text-sm">
            {content.tools_offered.map((tool) => tool.name).join(", ")}
          </p>
        </section>
      ) : null}
      {content.tool_calls.length > 0 ? (
        <section className="flex flex-col gap-1.5">
          <h3 className={label}>Tool calls</h3>
          <ol className="m-0 flex list-none flex-col gap-2.5 p-0">
            {content.tool_calls.map((toolCall, index) => (
              <li key={index} className="flex flex-col gap-1">
                <span className="text-sm font-medium">{toolCall.name}</span>
                <pre className={textBlock}>
                  {JSON.stringify(toolCall.arguments, null, 2)}
                </pre>
                <pre className={textBlock}>{toolCall.result}</pre>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      <section className="flex flex-col gap-1.5">
        <h3 className={label}>Response</h3>
        <pre className={textBlock}>{content.response || "—"}</pre>
      </section>
      {content.reasoning ? (
        <section className="flex flex-col gap-1.5">
          <h3 className={label}>Reasoning</h3>
          <pre className={textBlock}>{content.reasoning}</pre>
        </section>
      ) : null}
    </div>
  );
}
