import { useId } from "react";

import { LockIcon } from "@/components/LockIcon";
import { ModelCallContentDetails } from "@/components/ModelCallContentDetails";
import type { ModelCall } from "@/lib/api-client";
import {
  formatDuration,
  formatTokens,
  modelStepLabel,
  understandingShapeFacts,
} from "@/lib/model-calls";

/**
 * One model call in a trace: its step, model, tokens, time taken, the tools
 * it called, its error and the shape of its Understanding, then its content
 * when it was kept.
 *
 * @param props - `call` is the model call.
 * @returns The call's card.
 */
export function ModelCallCard({ call }: { call: ModelCall }) {
  const headingId = useId();
  const facts = [
    { label: "Model", value: call.model },
    {
      label: "Tokens",
      value: formatTokens(call.tokens_in, call.tokens_out),
    },
    { label: "Time taken", value: formatDuration(call.duration_ms) },
    {
      label: "Tools called",
      value: call.tools_called.length > 0 ? call.tools_called.join(", ") : "—",
    },
    ...(call.understanding_shape
      ? understandingShapeFacts(call.understanding_shape)
      : []),
  ];
  return (
    <article
      aria-labelledby={headingId}
      className="flex flex-col gap-4 rounded-card border border-line bg-white px-[22px] py-5"
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <h2 id={headingId} className="m-0 text-[17px] font-semibold">
          {modelStepLabel(call.step)}
        </h2>
        {call.error ? (
          <span className="inline-flex items-center rounded-full bg-danger-tint px-2.5 py-[3px] text-xs font-medium text-danger-deep">
            {call.error}
          </span>
        ) : null}
      </div>
      <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(min(160px,100%),1fr))] gap-3">
        {facts.map((fact) => (
          <div key={fact.label} className="flex flex-col gap-0.5">
            <dt className="text-caption text-ink-muted">{fact.label}</dt>
            <dd className="m-0 break-words">{fact.value}</dd>
          </div>
        ))}
      </dl>
      {call.content ? (
        <details>
          <summary className="cursor-pointer text-sm font-medium">
            Content
          </summary>
          <div className="pt-3">
            <ModelCallContentDetails content={call.content} />
          </div>
        </details>
      ) : (
        <p className="m-0 inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
          <LockIcon />
          No content kept for this User
        </p>
      )}
    </article>
  );
}
