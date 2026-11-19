import { CardTextField } from "@/components/CardTextField";

/**
 * A Memory Category's name and description, inside its card or the add
 * box.
 *
 * @param props - `name` and `description` are the text as edited;
 *   `onNameChange` and `onDescriptionChange` get the new text.
 * @returns The fields.
 */
export function MemoryCategoryFields({
  name,
  description,
  onNameChange,
  onDescriptionChange,
}: {
  name: string;
  description: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (description: string) => void;
}) {
  return (
    <>
      <CardTextField
        label="Name"
        hint="Users see this name on their Memories page."
        placeholder="e.g. Work"
        value={name}
        onChange={onNameChange}
      />
      <CardTextField
        label="Description"
        hint="Tells Zeph what belongs here."
        placeholder="Job, colleagues, career goals"
        value={description}
        multiline
        onChange={onDescriptionChange}
      />
    </>
  );
}
