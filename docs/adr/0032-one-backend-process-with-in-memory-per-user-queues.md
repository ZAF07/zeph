# One backend process, with in-memory per-User queues

Status: accepted. Numbered 0018 until 26 Nov 2026, when it became 0032 because another ADR also had 0018. Changed 26 Nov 2026: the tick was planned to run its items in parallel on its own pool, which was never built; the per-User reply locks were replaced by the queue's two lines (below).

For the MVP the backend stays a single process, sized to handle about 500 signed-up Users (25–50 chatting at once, some sending bursts of texts). Incoming messages wait their turn on a per-User queue held in memory, behind a port, and are worked on by a fixed thread pool of their own, apart from the web pool that serves webhooks and the Dashboard. The tick's items (ending quiet Conversations, processing ended ones, Portrait rewrites, Check-ins, Message Retention, deleting auth accounts) run one after another on the scheduler thread, and the next tick starts only once this one ends. The message pool size is a setting.

We chose this because nearly all the work waits on the model or Telegram, so one process with enough threads goes a long way. Before this, every message waiting for its User's turn held a web thread, so a few heavy texters could use up all 40 and freeze every chat and the Dashboard.

## Considered options

- **Queue in the database now** (an inbox table with workers claiming each User's messages). It survives restarts and works with 2+ backends, but it adds code and a database write and read per message before anything needs it. It is the adapter to add behind the same port when we run more than one backend (`.scratch/scaling/`).
- **Just raise the shared thread pool.** Rejected: chat and the Dashboard would still compete for the same threads.

## Consequences

- **A restart or deploy drops messages not yet answered**, and the User gets no reply to them. If Users report lost messages or the platform gets slow, look here first.
- Live replies come before tick work. A large tick makes Check-ins late, not double.
- Running a second backend process is still unsafe: the queue (with its guard on pending messages), sticker adding mode, typing, the timers and the scheduler all live in memory.
- Each User has two lines on the queue (built 23 Nov 2026, scaling issue 04, replacing two per-User locks): one handles what they send, one message at a time, and the other writes their replies one at a time. So a heavy texter holds at most two threads. A text is checked even while a reply is being written, and can drop that reply until any of it is sent (message pipeline issue 03). A message counts as not yet handled from when it arrives, so a reply waits for texts still in line.
- The message pool size is `MESSAGE_POOL_SIZE` (default 50). The webhook only looks up the sender's Telegram Connection and adds the message to the queue.
- `make load-test` (fake model and Telegram; real Postgres and embedder) is how we check that the sizing holds.
