import type {
  ApiClient,
  CaseResult,
  EvalName,
  FormShape,
  FormValues,
} from "@/lib/api-client";
import { evalOrder } from "@/lib/evals";

/** The Day Summary case shape, as the backend describes it. */
const daySummaryShape: FormShape = {
  sections: [
    {
      title: "The day",
      description:
        "The messages of one made-up day, in order. The memory processing step reads these to write the Day Summary.",
      fields: [
        {
          name: "messages",
          label: "Messages",
          description:
            "What the User and Zeph said that day, in order. Messages further apart than the Conversation quiet gap fall in separate Conversations, as they would on a real day.",
          kind: "group_list",
          required: true,
          options: [],
          unique_by: "",
          item_label: "Message",
          minimum: null,
          default: [],
          fields: [
            {
              name: "who",
              label: "From",
              description: "",
              kind: "choice",
              required: true,
              options: [
                { value: "person", label: "User" },
                { value: "zeph", label: "Zeph" },
              ],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "person",
            },
            {
              name: "time",
              label: "Time",
              description: "",
              kind: "time_of_day",
              required: true,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "",
            },
            {
              name: "text",
              label: "Text",
              description: "",
              kind: "long_text",
              required: true,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "",
            },
          ],
        },
      ],
    },
    {
      title: "Questions",
      description:
        "What the Summary must be able to answer: the facts, the feelings, and what Zeph offered and how it landed. The Judge sees only the Summary, never the messages.",
      fields: [
        {
          name: "questions",
          label: "Questions",
          description:
            "Each question and the answer the Summary should give. The case passes only if every answer matches.",
          kind: "group_list",
          required: true,
          options: [],
          unique_by: "",
          item_label: "Question",
          minimum: null,
          default: [],
          fields: [
            {
              name: "question",
              label: "Question",
              description: "",
              kind: "text",
              required: true,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "",
            },
            {
              name: "expected",
              label: "Expected answer",
              description: "",
              kind: "text",
              required: true,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "",
            },
          ],
        },
      ],
    },
  ],
};

/** The new Day Summary case drawn in `AdminEvalDaySummaryCase.html`. */
export const dayCaseDraft: { key: string; content: FormValues } = {
  key: "guilt-and-job-worry",
  content: {
    messages: [
      {
        who: "person",
        time: "9:10 AM",
        text: "I snapped at my sister again this morning and I feel awful about it.",
      },
      {
        who: "zeph",
        time: "9:12 AM",
        text: "That sounds heavy. What was going on just before you snapped?",
      },
    ],
    questions: [
      {
        question: "What did the User feel guilty about?",
        expected: "Snapping at their sister in the morning.",
      },
      {
        question: "What did Zeph offer, and how did it land?",
        expected:
          "A question about what happened just before. The User opened up about worry over their job.",
      },
    ],
  },
};

/** The result drawn under "How a result reads, on a run". */
export const dayCaseSampleResult: CaseResult = {
  id: "design-day-summary-result",
  variant: "A",
  try_number: 1,
  case_key: "guilt-and-job-worry",
  eval: "day_summary",
  outcome: "fail",
  checks: [],
  notes: [],
  error: "",
  tokens_in: 0,
  tokens_out: 0,
  duration_ms: 0,
  finished_at: "2026-11-19T21:00:00+08:00",
  day_summary: {
    summary:
      "Felt guilty about snapping at their sister in the morning. Later traced the short temper to worry about their job.",
    answers: [
      {
        question: "What did the User feel guilty about?",
        expected: "Snapping at their sister in the morning.",
        answer: "Snapping at their sister in the morning.",
        matched: true,
        reason: "The Summary states it directly.",
      },
      {
        question: "What did Zeph offer, and how did it land?",
        expected:
          "A question about what happened just before. The User opened up about worry over their job.",
        answer: "The Summary does not say what Zeph offered.",
        matched: false,
        reason:
          "The Summary records the job worry, and leaves out what Zeph offered and how the User took it.",
      },
    ],
  },
};

/**
 * The case shapes for the Day Summary case form; the other Evals have no
 * drawn form, so their shapes are empty.
 */
export const evalDaySummaryFixtures: Partial<ApiClient> = {
  listEvalCaseShapes: () =>
    Promise.resolve(
      Object.fromEntries(
        evalOrder.map((name) => [
          name,
          name === "day_summary" ? daySummaryShape : { sections: [] },
        ]),
      ) as Record<EvalName, FormShape>,
    ),
};
