import type { EvalCase, FormShape, ShapeField } from "@/lib/api-client";

/**
 * Builds a field of a case shape, for Dashboard tests.
 *
 * @param field - The parts that differ from an optional one-line text.
 * @returns The field.
 */
export function shapeField(
  field: Partial<ShapeField> & Pick<ShapeField, "name" | "label">,
): ShapeField {
  return {
    description: `What ${field.label} means.`,
    kind: "text",
    required: false,
    options: [],
    fields: [],
    unique_by: "",
    item_label: "",
    minimum: null,
    default: null,
    ...field,
  };
}

/** A small Persona-like case shape with two sections, for Dashboard tests. */
export const personaShape: FormShape = {
  sections: [
    {
      title: "Messages",
      description: "What the User sends, one after another.",
      fields: [
        shapeField({
          name: "messages",
          label: "Messages",
          kind: "group_list",
          required: true,
          item_label: "Message",
          default: [],
          fields: [
            shapeField({
              name: "text",
              label: "Text",
              kind: "long_text",
              description: "What the User writes, or the photo’s caption.",
              default: "",
            }),
          ],
        }),
      ],
    },
    {
      title: "What to expect",
      description: "The Judge reads the whole conversation.",
      fields: [
        shapeField({
          name: "photo_viewing",
          label: "Photo Viewing",
          kind: "on_off",
          description: "Whether the User has Photo Viewing on.",
          default: true,
        }),
        shapeField({
          name: "kind",
          label: "Label",
          kind: "choice",
          required: true,
          description: "Whether this message is a crisis.",
          options: [
            { value: "clear_crisis", label: "Clear crisis" },
            { value: "false_alarm", label: "False alarm" },
          ],
        }),
      ],
    },
  ],
};

/** A seeded Persona case, for Dashboard tests. */
export const smallTalkCase: EvalCase = {
  key: "small-talk",
  eval: "persona",
  content: {
    messages: [{ text: "hey there" }],
    photo_viewing: true,
    kind: "clear_crisis",
  },
  archived: false,
  edited: false,
  updated_at: "2026-11-15T09:00:00Z",
  updated_by_name: null,
};
