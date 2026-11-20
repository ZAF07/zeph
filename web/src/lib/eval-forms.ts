import {
  ApiError,
  type FormShape,
  type FormValues,
  type ShapeField,
} from "@/lib/api-client";

/**
 * The props every field of a shape-driven form takes. `inEntry` is true for
 * a field inside a list entry, whose input takes the panel colour.
 */
export type ShapeFieldProps = {
  field: ShapeField;
  value: unknown;
  path: string;
  errors: Record<string, string>;
  disabled: boolean;
  onChange: (value: unknown) => void;
  inEntry?: boolean;
};

const shortFieldKinds = new Set<ShapeField["kind"]>([
  "choice",
  "whole_number",
  "date_time",
  "time_of_day",
]);

/**
 * Says whether a field's value is short enough to sit beside others in a
 * row, as a message's From and Time do.
 *
 * @param field - The field.
 * @returns True for a choice, number, date or time.
 */
export function isShortField(field: ShapeField): boolean {
  return shortFieldKinds.has(field.kind);
}

/**
 * Names the button that adds an entry to a list, e.g. "Add a message" or
 * "Add an earlier line".
 *
 * @param itemLabel - What one entry is called, e.g. "Message".
 * @returns The button's text.
 */
export function addEntryLabel(itemLabel: string): string {
  const item = itemLabel.toLowerCase();
  return `Add ${/^[aeiou]/.test(item) ? "an" : "a"} ${item}`;
}

/**
 * Gives the value a new, empty field starts with.
 *
 * @param field - The field.
 * @returns Its default, or an empty value of its kind.
 */
export function emptyValue(field: ShapeField): unknown {
  if (field.kind === "group") {
    return emptyGroup(field.fields);
  }
  if (field.kind === "text_list" || field.kind === "group_list") {
    return [];
  }
  return field.default ?? null;
}

/**
 * Gives a new, empty group of fields, such as a new Message.
 *
 * @param fields - The group's fields.
 * @returns Each field's empty value by name.
 */
export function emptyGroup(fields: ShapeField[]): FormValues {
  return Object.fromEntries(
    fields.map((field) => [field.name, emptyValue(field)]),
  );
}

/**
 * Gives a new form's values: every field of the shape, empty.
 *
 * @param shape - The form's shape.
 * @returns The values.
 */
export function emptyForm(shape: FormShape): FormValues {
  return emptyGroup(shape.sections.flatMap((section) => section.fields));
}

/**
 * Says whether a value is a set of fields, like a group's value.
 *
 * @param value - The value.
 * @returns True for a plain object.
 */
export function isFormValues(value: unknown): value is FormValues {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Joins a field's name to the path of what it is in, as the backend writes
 * paths in its per-field messages.
 *
 * @param prefix - The path so far; "" at the top.
 * @param name - The field's name, or an entry's number in a list.
 * @returns E.g. `messages.0.text`.
 */
export function fieldPath(prefix: string, name: string | number): string {
  return prefix ? `${prefix}.${name}` : String(name);
}

/**
 * Reads what a refused form save said is wrong.
 *
 * @param error - The save's error, if any.
 * @returns `fields`, the message per field path, and `summary`, a line for
 *   the whole form; both empty when nothing was refused.
 */
export function savingErrors(error: unknown): {
  fields: Record<string, string>;
  summary: string | null;
} {
  if (!error) {
    return { fields: {}, summary: null };
  }
  if (error instanceof ApiError) {
    const { "": wholeForm, ...fields } = error.fields;
    return {
      fields,
      summary: wholeForm ?? error.detail ?? "Couldn’t save. Try again.",
    };
  }
  return { fields: {}, summary: "Couldn’t save. Try again." };
}
