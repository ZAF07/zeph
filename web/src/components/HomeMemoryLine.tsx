import { readCopy, type Copy } from "@/lib/copy";

/**
 * The line on the Dashboard home about User Memory. While it is on, it says
 * so; while it is off, it shows the Admin-worded note saying why, with the
 * text between double asterisks in the brighter colour.
 *
 * @param props - `copy` is Home's Copy; `note` is the note the backend
 *   sent, "" while User Memory is on.
 * @returns The line.
 */
export function HomeMemoryLine({ copy, note }: { copy: Copy; note: string }) {
  return (
    <p
      role={note ? "status" : undefined}
      className="m-0 rounded-note border border-line px-5 py-3.5 text-[14px] text-soft"
    >
      {note ? (
        note.split("**").map((part, index) =>
          index % 2 === 1 ? (
            <span key={index} className="text-text">
              {part}
            </span>
          ) : (
            part
          ),
        )
      ) : (
        <>
          <span className="text-text">
            {readCopy(copy, "home.memory.on_title")}
          </span>{" "}
          {readCopy(copy, "home.memory.on_body")}
        </>
      )}
    </p>
  );
}
