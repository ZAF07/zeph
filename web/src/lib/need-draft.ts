import type { NeedInput } from "@/lib/api-client";

/**
 * Says whether a Need was edited, ignoring the order of its rule-outs.
 *
 * @param draft - The Need as edited.
 * @param saved - The Need as saved.
 * @returns True when any field differs.
 */
export function isNeedChanged(draft: NeedInput, saved: NeedInput): boolean {
  const ruledOut = new Set(draft.ruled_out_move_ids);
  return (
    draft.name !== saved.name ||
    draft.when_it_fits !== saved.when_it_fits ||
    draft.how_to_reply !== saved.how_to_reply ||
    ruledOut.size !== saved.ruled_out_move_ids.length ||
    saved.ruled_out_move_ids.some((id) => !ruledOut.has(id))
  );
}

/**
 * Says whether a Need has everything it needs to be saved.
 *
 * @param need - The Need as edited.
 * @returns True when its name and both texts are filled in.
 */
export function isNeedComplete(need: NeedInput): boolean {
  return (
    need.name.trim() !== "" &&
    need.when_it_fits.trim() !== "" &&
    need.how_to_reply.trim() !== ""
  );
}
