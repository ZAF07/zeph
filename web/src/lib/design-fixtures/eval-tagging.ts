import type { CaseResult, FormShape, FormValues } from "@/lib/api-client";

/** The Tagging case shape, as the backend describes it. */
export const taggingShape: FormShape = {
  sections: [
    {
      title: "When",
      description: "The time the ended Conversation started.",
      fields: [
        {
          name: "now",
          label: "When the first message was sent",
          description:
            "In UTC, which is also the User's time zone. The messages come a minute apart from it.",
          kind: "date_time",
          required: true,
          options: [],
          fields: [],
          unique_by: "",
          item_label: "",
          minimum: null,
          default: null,
        },
      ],
    },
    {
      title: "Life Threads it touched",
      description:
        "The made-up User's Life Threads this Conversation started, changed or brought up. The tagging step is shown them numbered, in this order.",
      fields: [
        {
          name: "threads",
          label: "Life Threads",
          description: "Leave empty when the Conversation touched none.",
          kind: "group_list",
          required: false,
          options: [],
          fields: [
            {
              name: "title",
              label: "Title",
              description: "The Thread's title.",
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
              name: "story",
              label: "Story",
              description: "What happened so far.",
              kind: "long_text",
              required: true,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "",
            },
            {
              name: "people",
              label: "People",
              description: "The people or things in it, e.g. Mei.",
              kind: "text_list",
              required: false,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "Person",
              minimum: null,
              default: [],
            },
          ],
          unique_by: "",
          item_label: "Life Thread",
          minimum: null,
          default: [],
        },
      ],
    },
    {
      title: "The ended Conversation",
      description:
        "Every message, oldest first. The real tagging step reads all of it, with the whole Pattern Catalog, when the Conversation ends.",
      fields: [
        {
          name: "messages",
          label: "Messages",
          description:
            "What the User and Zeph said, in order. Only the User's own words can be quoted.",
          kind: "group_list",
          required: true,
          options: [],
          fields: [
            {
              name: "who",
              label: "From",
              description: "",
              kind: "choice",
              required: true,
              options: [
                {
                  value: "person",
                  label: "User",
                },
                {
                  value: "zeph",
                  label: "Zeph",
                },
              ],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "person",
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
          unique_by: "",
          item_label: "Message",
          minimum: null,
          default: [],
        },
      ],
    },
    {
      title: "Observations to expect",
      description:
        "What code must keep after its checks. The case passes only when every one below is kept and nothing else is. Leave empty when there is nothing to tag.",
      fields: [
        {
          name: "observations",
          label: "Observations",
          description:
            "Several quotes kept for one Observation below still match it.",
          kind: "group_list",
          required: false,
          options: [],
          fields: [
            {
              name: "pattern_type",
              label: "Pattern Type",
              description:
                "Its ID in the Pattern Catalog, e.g. CONF.AVOID.BELONG. When unclear, either of the two.",
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
              name: "direction",
              label: "For or against",
              description:
                "Whether it counts for the Pattern Type or against it.",
              kind: "choice",
              required: true,
              options: [
                {
                  value: "for",
                  label: "For",
                },
                {
                  value: "against",
                  label: "Against",
                },
              ],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: "for",
            },
            {
              name: "unclear",
              label: "Unclear",
              description:
                "On when it could be either of two look-alike Pattern Types.",
              kind: "on_off",
              required: false,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: false,
            },
            {
              name: "situational",
              label: "Anyone would",
              description:
                "On when anyone would have acted the same there, so it counts for nothing.",
              kind: "on_off",
              required: false,
              options: [],
              fields: [],
              unique_by: "",
              item_label: "",
              minimum: null,
              default: false,
            },
          ],
          unique_by: "",
          item_label: "Observation",
          minimum: null,
          default: [],
        },
      ],
    },
  ],
};

/** The new Tagging case drawn in `AdminEvalTaggingCase.html`. */
export const taggingCaseDraft: { key: string; content: FormValues } = {
  key: "conf-yes-to-sister-then-resents",
  content: {
    now: "2026-11-24T10:00:00",
    threads: [
      {
        title: "Helping Mei move",
        story: "Their sister Mei keeps asking for help moving flats.",
        people: ["Mei"],
      },
    ],
    messages: [
      {
        who: "person",
        text: "Mei asked me to help her move again this Saturday. I said yes straight away even though I’d planned to rest.",
      },
      {
        who: "zeph",
        text: "That’s a lot to give up a rest day for. What made you say yes?",
      },
    ],
    observations: [
      {
        pattern_type: "CONF.AVOID.BELONG",
        direction: "for",
        unclear: false,
        situational: false,
      },
    ],
  },
};

/** The result drawn under "How a result reads, on a run". */
export const taggingCaseSampleResult: CaseResult = {
  id: "design-tagging-result",
  variant: "A",
  try_number: 1,
  case_key: "conf-yes-to-sister-then-resents",
  eval: "tagging",
  outcome: "fail",
  checks: [],
  notes: [],
  error: "",
  tokens_in: 0,
  tokens_out: 0,
  duration_ms: 0,
  finished_at: "2026-11-24T21:00:00+08:00",
  tagging: {
    answered: true,
    expected: [
      {
        pattern_type: "CONF.AVOID.BELONG",
        direction: "for",
        unclear: false,
        situational: false,
        matched: true,
      },
    ],
    kept: [
      {
        pattern_types: ["CONF.AVOID.BELONG"],
        sign: "I2",
        direction: "for",
        unclear: false,
        situational: false,
        quote: "I said yes straight away even though I’d planned to rest",
        context: "Agreed to help Mei move again, giving up a rest day.",
        about: "Mei, their sister",
        thread: "Helping Mei move",
        expected: true,
      },
      {
        pattern_types: ["ACH.WORTH.PERF"],
        sign: "I4",
        direction: "for",
        unclear: false,
        situational: false,
        quote: "I’d planned to rest",
        context: "Gave up rest to be useful.",
        about: "themselves",
        thread: null,
        expected: false,
      },
    ],
    dropped: [
      {
        pattern_types: ["CONF.AVOID.BELONG"],
        sign: "I5",
        direction: "for",
        quote: "it’s fine, not a big deal",
        reason: "quote not word for word in the User's own texts",
      },
    ],
    unclear: [],
  },
};
