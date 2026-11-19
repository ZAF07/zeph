import { readCopy, type Copy } from "@/lib/copy";

/**
 * The line on the Dashboard home saying User Memory is on.
 *
 * @param props - `copy` is Home's Copy.
 * @returns The line.
 */
export function HomeMemoryLine({ copy }: { copy: Copy }) {
  return (
    <p className="m-0 rounded-note border border-line px-5 py-3.5 text-[14px] text-soft">
      <span className="text-text">
        {readCopy(copy, "home.memory.on_title")}
      </span>{" "}
      {readCopy(copy, "home.memory.on_body")}
    </p>
  );
}
