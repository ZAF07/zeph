import { readFile } from "node:fs/promises";
import path from "node:path";

import { compile } from "tailwindcss";
import { describe, expect, it } from "vitest";

const appFolder = path.join(process.cwd(), "src/app");

/**
 * Finds a stylesheet the way the app's build does: `tailwindcss` from its
 * package, anything else relative to the file importing it.
 *
 * @param id - The imported path.
 * @param base - The folder of the importing file.
 * @returns The stylesheet's text and folder.
 */
async function loadStylesheet(id: string, base: string) {
  const file =
    id === "tailwindcss"
      ? path.join(process.cwd(), "node_modules/tailwindcss/index.css")
      : path.resolve(base, id);
  return {
    path: file,
    base: path.dirname(file),
    content: await readFile(file, "utf8"),
  };
}

/**
 * Builds the CSS the app's theme gives for some class names.
 *
 * @param classNames - The classes to build.
 * @returns The generated CSS.
 */
async function buildClasses(classNames: string[]): Promise<string> {
  const globals = await readFile(path.join(appFolder, "globals.css"), "utf8");
  const compiler = await compile(globals, { base: appFolder, loadStylesheet });
  return compiler.build(classNames);
}

describe("the Zeph theme", () => {
  it("gives the design tokens' colours", async () => {
    const css = await buildClasses(["bg-cream", "text-ink", "border-line"]);

    expect(css).toContain("--color-cream: #f3e8d6");
    expect(css).toContain(".bg-cream");
    expect(css).toContain(".text-ink");
    expect(css).toContain(".border-line");
  });

  it("resolves none of Tailwind's default colours", async () => {
    const css = await buildClasses([
      "bg-red-500",
      "text-gray-700",
      "border-slate-200",
      "bg-blue-600",
    ]);

    expect(css).not.toMatch(/bg-red-500|text-gray-700|border-slate-200/);
    expect(css).not.toContain("bg-blue-600");
  });

  it("sets the sans font to Outfit", async () => {
    const css = await buildClasses(["font-sans"]);

    expect(css).toContain("--font-sans: var(--font-outfit), system-ui");
  });
});
