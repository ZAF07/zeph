# Each Eval's case shape checks saves and draws the Dashboard form

Admins edit the six Evals' cases on the Dashboard (ADR-0004), and each Eval's cases look different. Instead of six hand-built pages, core describes each Eval's case shape once, as sections of fields with a label, a plain description and a kind (text, number, on/off, choice, date, image, list, group), and the same description checks every save (a message per field path, e.g. `messages.0.text`) and is sent to the Dashboard, which draws the form from it with no rules of its own. The Judge's settings use the same kind of shape. So a field can't be checked by the backend without appearing, explained, on the form, and a new field is a change in one place.

## Consequences

- Case content is stored in the plain shape the forms write (lists of `{id, check}` rules, `{category, contents}` Memory Items, `{who, text}` earlier lines, Persona messages as `{text, photo, shows}`). The seed files keep their shorter YAML and are rewritten into this shape when read; run snapshots from before the change keep the old shape.
- Checks that span fields (a Life Thread's title written elsewhere, forgetting a Memory Item the case doesn't have) stay in each Eval's case reader and run after the shape check, pointing at the field they're about.
