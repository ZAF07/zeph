# Shared Photos are seen through one photo service and kept on Telegram

The Companion views the photos Users send. One core service looks at each photo when it arrives and writes a detailed description; everything else (Safeguard, replies, User Memory, Check-ins) works from that text. The photo is looked at again only when the description can't answer, through an `ask_about_photo` tool that also goes through this service. We keep only Telegram's file id and download the photo from Telegram when needed, never storing the image ourselves. We chose this so the Safeguard checks photos without changes, the reply model doesn't need image support, image costs are paid once, and we hold no copies of Users' private images.

## Considered Options

- **Reply model sees every photo directly**: rejected. It needs a vision model for replies, pays for the image on every reply, and the Safeguard would still need text.
- **Storing image bytes ourselves**: rejected. More private data to secure and delete, when Telegram already keeps the photo.
- **Reverse image search** (sending a photo to a search service): rejected for the MVP for privacy, because it sends a User's private photo to a third party and could identify people in it. Web Search about a photo uses words from its description, and the Companion never tries to identify a person. Revisit after the MVP to improve the product.

- **Keeping every photo**: rejected. It piles up sensitive screenshots (bank statements, tickets) forever and fills the Dashboard and Check-ins with junk. Instead, memory processing picks the photos that matter to the User when the Conversation ends, and adds a note on why each matters. The rest are used only in their Conversation.

## Consequences

- Each User has a Photo Viewing setting, on by default. Off means the Companion doesn't look at their photos at all: no description, nothing kept, and their Shared Photos aren't used or sent back (but aren't deleted). The caption is still answered, and the Companion says honestly that it didn't view the photo. Users change it on the Dashboard or in chat, adding it to the chat settings in ADR 0006.
- A photo is a normal Telegram photo or a JPEG, PNG or WebP image sent as a file (up to Telegram's 20 MB bot download limit). GIFs, videos, voice notes and other files stay Unsupported Messages.
- Later, for a higher plan: Users may send text files in chat, which are read and answered in the normal reply flow. That will be its own Feature.
- Every photo is always checked by the Safeguard, even when Photo Viewing is off for the User, by an Admin or for everyone. Then the photo is used only for that check: the reply ignores it and nothing is kept. User safety comes first, and Users are told this plainly where they switch Photo Viewing.
- Photo Viewing is one feature behind one switch so it can later move to a paid plan. In the MVP every User has it.

- If Telegram stops serving an old file id, the photo can't be looked at or sent again; its description still works.
- Delete My Data removes our file ids and descriptions, but the photo stays in the User's own Telegram chat, which they control.
