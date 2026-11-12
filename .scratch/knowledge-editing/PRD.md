# PRD: View and edit Knowledge Documents

Status: ready-for-agent

## Problem Statement

Admins can upload, list, retry and delete Knowledge Documents, but they cannot see what a document actually says or change anything about it. To fix a typo in a title, correct a source, move a document to another tradition, trim a passage that keeps pulling the Companion off course, or swap in a better translation, an Admin has to delete the document and upload it again. That loses the document's history (when it was added), forces them to keep the original file around, and gives no way at all to check what text was read out of a PDF. A scanned PDF that failed ("Scanned PDF — no text found") can only be thrown away, even when the Admin could simply type or paste its text.

## Solution

Each Knowledge Document gets its own page in the admin area. From the Knowledge list, an Admin opens a document and sees its details (title, source / author, tradition, type, status, when it was added) and the full text the Companion draws on. They can:

- edit the title, source / author and tradition, which takes effect straight away;
- edit the text itself, which re-indexes the document (Pending → Ready / Failed) so replies use the new wording;
- replace the file with a new text, Markdown or PDF file, which reads the new file's text and re-indexes the document, keeping its identity and when it was added;
- give a failed document its text by hand (for example, paste the text of a scanned PDF), which makes it Ready.

Delete and Retry stay as they are.

## User Stories

1. As an Admin, I want to open a Knowledge Document from the Knowledge list, so that I can look at one document in detail.
2. As an Admin, I want to see a document's title, source / author, tradition, type, status and when it was added on its page, so that I have everything about it in one place.
3. As an Admin, I want to read the full text the Companion draws on for a document, so that I can check what was actually read out of the file.
4. As an Admin, I want to see a PDF's text as it was read, so that I can spot pages that came out garbled or empty.
5. As an Admin, I want to see why a document failed on its page, so that I know what to fix.
6. As an Admin, I want to change a document's title, so that typos and unclear titles can be fixed.
7. As an Admin, I want to change a document's source / author, so that attribution is correct.
8. As an Admin, I want to change a document's tradition, so that it is filed correctly.
9. As an Admin, I want title, source and tradition changes to take effect immediately, without re-indexing, so that small fixes are instant.
10. As an Admin, I want the Companion's replies to show the new title and source as soon as I save them, so that it never cites stale details.
11. As an Admin, I want to be told when a title, source or tradition is blank, so that I don't save an incomplete document.
12. As an Admin, I want to edit a document's text, so that I can trim, correct or tidy what the Companion draws on.
13. As an Admin, I want saving edited text to re-index the document, so that replies use the new wording.
14. As an Admin, I want the document to show Pending while it is re-indexed and Ready when it is done, so that I know when the change is live.
15. As an Admin, I want a re-index that fails after an edit to show Failed with the reason, so that I can retry it.
16. As an Admin, I want Retry on a document whose text I edited to re-index my edited text, not the original file, so that my edits are never lost.
17. As an Admin, I want to be told when I try to save blank text, so that I don't accidentally empty a document.
18. As an Admin, I want to be warned before leaving the page with unsaved text changes, so that I don't lose an edit by mistake.
19. As an Admin, I want to replace a document's file with a new text, Markdown or PDF file, so that I can swap in a better translation or a corrected version.
20. As an Admin, I want replacing the file to keep the document's title, source, tradition and added date unless I change them, so that I don't have to re-enter its details.
21. As an Admin, I want replacing the file to read the new file's text and re-index it, so that replies use the new version.
22. As an Admin, I want a replaced file that can't be read (scanned, broken or not UTF-8) to show Failed with the same reasons as an upload, so that I know what went wrong.
23. As an Admin, I want the same file rules on replace as on upload (text, Markdown or PDF, up to 20 MB, not empty), so that the library stays consistent.
24. As an Admin, I want to type or paste the text of a document that failed because its PDF had no text, so that a scanned document can still be used.
25. As an Admin, I want a document whose text I typed in to become Ready like any other, so that it is used in replies.
26. As an Admin, I want the document's type to still show the type of the file it came from, so that I know where it started.
27. As an Admin, I want to see whether a document's text has been edited since its file was read, so that I know it no longer matches the file word for word.
28. As an Admin, I want to delete a document from its page too, so that I don't have to go back to the list.
29. As an Admin, I want to retry a failed document from its page, so that I can fix and retry in one place.
30. As an Admin, I want the document page to keep checking while the document is Pending, so that I see it become Ready without reloading.
31. As an Admin, I want a clear message when a document no longer exists (for example, another Admin deleted it), so that I am not left on a broken page.
32. As an Admin, I want only Admins to be able to view or change a document's text, so that the library stays curated.
33. As a User, I want the Companion to draw on the corrected wording once an Admin fixes a document, so that what it shares is accurate.
34. As a User, I want the Companion never to draw on half-updated Knowledge while a document is being re-indexed, so that it doesn't mix old and new versions.
35. As an Admin, I want documents that existed before this feature to show their text too, so that the whole library can be viewed and edited, not just new uploads.
36. As an Admin, I want the starter documents to be viewable and editable like any other, so that I can adjust the summaries drafted for me.
37. As an Admin, I want to read and edit a document's text in a proper editor, not a plain text box, so that working on long texts is comfortable.
38. As an Admin, I want line numbers, soft line wrapping and Markdown highlighting in the editor, so that I can find my place and see structure at a glance.
39. As an Admin, I want a toolbar for headings, bold, italic, quotes and lists, so that I can format Markdown without remembering its syntax.
40. As an Admin, I want to find and replace within a document's text, so that I can fix a repeated word or name in one go.
41. As an Admin, I want undo and redo in the editor, so that I can back out of a mistake.
42. As an Admin, I want to switch between Edit, Preview and side-by-side views, so that I can see how the Markdown reads while I write it.
43. As an Admin, I want to see the word and character count, so that I know how long a document is.
44. As an Admin, I want a clear "Unsaved changes" indicator, so that I always know whether what I see is saved.
45. As an Admin, I want to save with Ctrl/⌘+S, so that saving feels like any other editor.
46. As an Admin, I want to review a side-by-side or inline comparison of my changes before saving, so that I re-index only what I meant to change.
47. As an Admin, I want to discard my unsaved changes in one step, after confirming, so that I can start over.
48. As an Admin, I want to view the text in the same editor, read-only, with find, so that reading a long document is as easy as editing it.
49. As an Admin, I want the editor to stay quick on long documents (tens of thousands of characters), so that the larger starter texts are pleasant to work on.
50. As an Admin, I want the editor to work with the keyboard alone and with a screen reader, and to stack sensibly on a phone, so that it is usable by everyone, everywhere.

## Implementation Decisions

- **A Knowledge Document's text becomes stored data.** Today ingestion reads the file's text and keeps only the chunks. From now on the text read from the file is saved on the document, and it is what the Companion draws on: chunking and embedding always work from the saved text. The uploaded file is kept as the document's source.
- **Ingestion splits into two steps.** (1) *Read*: get the text out of the file through the text extractor and save it on the document; failures here are the existing reasons ("Couldn’t read this PDF.", "Scanned PDF — no text found", the UTF-8 message). (2) *Index*: chunk, embed and store the saved text; failure here is the existing "Couldn’t index the document. Try again." Upload and replace file run both steps; editing the text runs only *Index*.
- **Retry** re-runs whichever step is needed: if the document has saved text (read succeeded, or the Admin typed it), only *Index*; otherwise *Read* then *Index*. Edited text is therefore never overwritten by re-reading the original file.
- **Edited flag.** The document records whether its text was edited by an Admin after it was last read from a file; replacing the file clears it.
- **Editing details** (title, source / author, tradition) is a plain update with the same validation as upload (trimmed, not blank). No re-index: replies look up details from the document when composing, so they show the new details straight away.
- **Editing text** saves the trimmed text (not blank), sets the document Pending, clears any failure reason, and indexes in the background like upload does. Editing the text of a Failed document is allowed and is how a scanned PDF gets its text.
- **Replacing the file** keeps the document's ID, details and added date, stores the new file and its type, sets it Pending, and runs *Read* then *Index* in the background. File rules are the same as upload.
- **While Pending, the document is not used in replies** (unchanged rule: only Ready documents are used). Its old chunks are swapped for the new ones in one step only when indexing succeeds.
- **Interrupted work.** The existing start-up step that finishes Pending documents applies to edits and replacements too, using the same Retry rule.
- **Existing documents.** Documents from before this feature have no saved text. On start-up, the backend reads the text from each such document's file and saves it, without re-indexing. A document that never read successfully stays as it is; Retry handles it.
- **Schema:** Knowledge documents gain the document's text (nullable until read) and an "edited" flag. No change to chunks.
- **Ports:** no new ports. The Knowledge Document repository gains operations to read one document with its text, update details, save text (with the edited flag), and replace the file. The text extractor, embedder and vector store are unchanged.
- **API (Admin, role checked on the router, JSON unless noted):**
  - `GET /api/admin/knowledge-documents/{id}` — the document with its `text` (null if never read) and `text_edited`; 404 if missing. The list endpoint stays without text, so the list stays light.
  - `PATCH /api/admin/knowledge-documents/{id}` — `{title?, source?, tradition?}`; 422 if a given field is blank; 404 if missing; returns the document.
  - `PUT /api/admin/knowledge-documents/{id}/text` — `{text}`; 422 if blank; 404 if missing; returns the Pending document; indexes in the background.
  - `PUT /api/admin/knowledge-documents/{id}/file` — multipart `file`; 422 for wrong type, empty or over 20 MB; 404 if missing; returns the Pending document; reads and indexes in the background.
  - Upload, list, retry and delete are unchanged, except that Retry follows the rule above.
- **Dashboard:** a document page at `/admin/knowledge/<id>`, reached from the title in each row of the Knowledge table. It has a details form (Save), the text in the Knowledge text editor (below; Save text says it will re-index), Replace file (same drop area and rules as upload), Retry when Failed, Delete (confirm, then back to the list), status pill and failure reason, an "Edited" marker, checking again while Pending, and loading / not-found / error states. All calls go through the API client.
- **Knowledge text editor (must be professional, not a plain text box).** One editor component, used read-only for viewing (issue 01) and editable for editing (issue 03). Built on CodeMirror 6 (a mature, accessible, fast editor that handles long texts), styled to the Zeph design tokens. It has:
  - line numbers, soft wrap, Markdown syntax highlighting, active-line highlight and a visible focus ring;
  - a toolbar: Heading, Bold, Italic, Quote, Bulleted list, Numbered list, Undo, Redo, Find & replace — each with a tooltip and keyboard shortcut;
  - an Edit / Preview / Split view switch; Preview renders the Markdown safely (no raw HTML) in Zeph's type styles; on narrow screens Split falls back to the Edit / Preview switch;
  - a status bar with word and character count, "Unsaved changes" / "Saved" state and the document status;
  - Ctrl/⌘+S to save; "Discard changes" with confirmation; a warning before leaving with unsaved changes;
  - "Review changes" before saving: a comparison of saved and edited text (additions and removals highlighted), then "Save and re-index";
  - read-only mode keeps find, line numbers and Preview but hides editing controls;
  - full keyboard use and screen-reader labels; stays responsive on the largest starter document (~42,000 characters).
  The editor is a client component kept behind its own small interface (value, onChange, readOnly), so pages and tests don't depend on CodeMirror directly.
- **Design:** the admin design has no document page; it follows the existing Knowledge screen and admin form styles. Nothing tagged "Later" is involved.
- **Domain language:** update the Knowledge Document entry in `CONTEXT.md` to say its text is viewable and editable by Admins and that editing it makes the document Pending until re-indexed.

## Testing Decisions

- Good tests check behaviour from the outside: send a request, then check what the API returns, what the next reply's instructions contain, or what is stored. They don't check which internal function ran, so restructuring the ingestion steps must not break them.
- **Seam 1 (main seam): the backend HTTP surface** through FastAPI's test client, real Postgres (test container), real pgvector and text extractor, fake embedder and scripted chat model — exactly as in the existing Knowledge tests. Cover:
  - view: details plus the text read from a txt, Markdown and PDF upload; 404 for a missing document; non-Admins get 403 on every new route;
  - edit details: saved and listed; blank refused; the next reply cites the new title without a re-index;
  - edit text: returns Pending, becomes Ready, `text_edited` true; the next reply contains the new wording and not the old; blank refused;
  - edit text on a failed scanned PDF makes it Ready;
  - Retry after a failed re-index of edited text keeps the edited text;
  - replace file: keeps ID, details and added date; new type; new text in replies; old text gone; `text_edited` cleared; unreadable replacement fails with the existing reasons; file rules enforced;
  - a document left Pending by an interrupted edit is finished on start-up; documents with no saved text get it on start-up.
- **Seam 3: the Dashboard** with Vitest and React Testing Library, API client mocked: the document page shows details and text, saves details, saves text through the editor (Unsaved indicator, Review changes, Ctrl/⌘+S, Discard, Preview renders Markdown, word count; shows Pending, then Ready), replaces the file, shows a backend refusal reason, Retry and Delete, the Edited marker, not-found and load-error states; the Knowledge table links each title to its page.
- **Prior art:** the existing Knowledge seam 1 tests and helpers (upload, list, PDF builders, reply-instructions helper), the Knowledge seed tests for start-up behaviour, and the existing Knowledge library component tests for seam 3.
- No new adapter contract tests: no adapter changes.

## Out of Scope

- Version history or undo of past edits.
- A WYSIWYG (rich-text) editor; the text stays Markdown, edited in a code-style editor with Preview.
- Collaborative real-time editing.
- Downloading the original file.
- Editing individual chunks or choosing where chunks split.
- Admin-managed list of traditions.
- Bulk edits across several documents.
- Showing which passages were used in which replies.

## Further Notes

- Builds on issue 08 (archived: `.scratch/mvp/issues/archive/08-knowledge.md`) and MVP PRD user stories 74–75.
- Two Admins editing the same document at once: the last save wins, as with other admin settings.
- The "Owner’s summary" starter documents were drafted for the owner to review; this feature is how they will be adjusted.
