import type { MoveInput } from "@/lib/api-client";

/**
 * Says whether a Move was edited.
 *
 * @param draft - The Move as edited.
 * @param saved - The Move as saved.
 * @returns True when any field differs.
 */
export function isMoveChanged(draft: MoveInput, saved: MoveInput): boolean {
  return (
    draft.name !== saved.name ||
    draft.when_it_fits !== saved.when_it_fits ||
    draft.how_to_do_it !== saved.how_to_do_it ||
    draft.needed_feature !== saved.needed_feature ||
    draft.asks_a_question !== saved.asks_a_question
  );
}

/**
 * Says whether a Move has everything it needs to be saved.
 *
 * @param move - The Move as edited.
 * @returns True when its name and both texts are filled in.
 */
export function isMoveComplete(move: MoveInput): boolean {
  return (
    move.name.trim() !== "" &&
    move.when_it_fits.trim() !== "" &&
    move.how_to_do_it.trim() !== ""
  );
}

/**
 * Picks a Move's own fields, leaving out its id.
 *
 * @param move - The Move as edited.
 * @returns The fields the backend saves.
 */
export function moveInputOf(move: MoveInput): MoveInput {
  return {
    name: move.name,
    when_it_fits: move.when_it_fits,
    how_to_do_it: move.how_to_do_it,
    needed_feature: move.needed_feature,
    asks_a_question: move.asks_a_question,
  };
}
