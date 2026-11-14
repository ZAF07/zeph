# Core errors say their kind; HTTP maps each kind once

Every error core raises for a refused request inherits from one kind in `core/errors.py`: not found, not allowed, invalid, conflict or outside service. The HTTP adapter registers one handler per kind (404, 403, 422, 409, 502) and routes never catch core errors. The text a person sees lives on the error, in core. We chose this because about 100 hand-written `HTTPException` mappings let status codes drift between routes, and a new error or route had to remember the mapping.

## Consequences

- A new core error gets the right status code from its base class alone; a test checks each existing error's status and exact body.
- People-facing error text is in core, beside the rule that raises it, so the chat channel and the Dashboard can share it. An error sets fixed text with `shown_message`, or is raised with text that names the thing (e.g. a sticker set's name, or which last-Admin change was refused).
- Routes call core and turn the result into a response. Pages that combine several things (Home, the Check-ins page, `/me`, platform content) are put together in core, so routes don't read platform settings.
- Errors that never reach HTTP (e.g. a model's unusable answer) don't need a kind.
