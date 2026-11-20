import { useId } from "react";

import { LockIcon } from "@/components/LockIcon";
import { ModelCallContentDetails } from "@/components/ModelCallContentDetails";
import { StatusPill } from "@/components/StatusPill";
import type { ModelCall } from "@/lib/api-client";
import {
  checkInShapeFacts,
  formatDuration,
  formatTokens,
  modelStepLabel,
  replyPlanShapeFacts,
  understandingShapeFacts,
} from "@/lib/model-calls";

/**
 * One model call in a trace: its step, model, tokens, time taken, the tools
 * it called, its error and the shape of its Understanding, Reply Plan or
 * woven-in Check-in decision, then its content when it was kept.
 *
 * @param props - `call` is the model call.
 * @returns The call's card.
 */
export function ModelCallCard({ call }: { call: ModelCall }) {
  const headingId = useId();
  const facts = [
    { label: "Model", value: call.model },
    { label: "Thinking", value: call.thinking ? "On" : "Off" },
    {
      label: "Tokens",
      value: formatTokens(call.tokens_in, call.tokens_out),
    },
    { label: "Time taken", value: formatDuration(call.duration_ms) },
    {
      label: "Tools called",
      value:
        call.tools_called.length > 0 ? call.tools_called.join(", ") : "None",
    },
    ...(call.understanding_shape
      ? understandingShapeFacts(call.understanding_shape)
      : []),
    ...(call.reply_plan_shape
      ? replyPlanShapeFacts(call.reply_plan_shape)
      : []),
    ...(call.check_in_shape ? checkInShapeFacts(call.check_in_shape) : []),
  ];
  return (
    <article
      aria-labelledby={headingId}
      className="flex flex-col gap-4 rounded-card border border-line bg-panel px-6 py-[22px] text-[14px] text-text"
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <h2 id={headingId} className="m-0 text-[17px] font-normal text-cream">
          {modelStepLabel(call.step)}
        </h2>
        {call.error ? (
          <StatusPill filled={false} danger>
            {call.error}
          </StatusPill>
        ) : null}
      </div>
      <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(min(160px,100%),1fr))] gap-3">
        {facts.map((fact) => (
          <div key={fact.label} className="flex flex-col gap-0.5">
            <dt className="text-[13px] text-soft">{fact.label}</dt>
            <dd className="m-0 break-words">{fact.value}</dd>
          </div>
        ))}
      </dl>
      {call.content ? (
        <details className="group">
          <summary className="cursor-pointer list-none text-[14px] text-text [&::-webkit-details-marker]:hidden">
            <span
              aria-hidden="true"
              className="inline-block w-4 text-soft group-open:hidden"
            >
              ▸
            </span>
            <span
              aria-hidden="true"
              className="hidden w-4 text-soft group-open:inline-block"
            >
              ▾
            </span>
            Content
          </summary>
          <div className="pt-3">
            <ModelCallContentDetails content={call.content} />
          </div>
        </details>
      ) : (
        <p className="m-0 inline-flex items-center gap-1.5 text-[12px] text-soft">
          <LockIcon />
          No content kept for this User
        </p>
      )}
    </article>
  );
}
