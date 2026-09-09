# Working with websockets

Baserow uses [Django Channels](https://channels.readthedocs.io/en/latest/) library to handle websocket connections.

## Consumers

The communication between connected clients (like the Baserow web-frontend) and Baserow backend is done through Django Channels [consumers](https://channels.readthedocs.io/en/latest/topics/consumers.html). A consumer is akin to a Django view. It can receive payloads from a client and send payloads to the client. The difference is that consumers are stateful and handle communication back and forth for the whole duration of a websocket connection.

Similarly to Django views, consumers are hooked to a particular URL, see this excerpt from `backend/src/baserow/ws/routing.py` on how the `CoreConsumer` is routed:

```python
websocket_urlpatterns = [re_path(r"^ws/core/", CoreConsumer.as_asgi())]
```

The above example shows that any client that wants to establish a websocket connection using the `ws/core/` URL (with ws protocol) will be handled by the `CoreConsumer`.

Each consumer has access to the connection’s [scope](https://channels.readthedocs.io/en/latest/topics/consumers.html#scope) which is like the `request` object in traditional views, holding various information about the connection.

### AsyncJsonWebsocketConsumer

We use [`AsyncJsonWebsocketConsumer`](https://channels.readthedocs.io/en/latest/topics/consumers.html#asyncjsonwebsocketconsumer) from the Django Channels library as the base for our consumers since we want to exchange JSON payloads. These consumers typically have three main event handlers: `connect` (for setting up the connection or revoking the connection), `disconnect` (for cleanup), and `receive_json` (for reacting to client's messages).

In each AsyncJsonWebsocketConsumer, we will typically want to:

- React to client's messages in `receive_json`
- Send messages back to the connected client via `self.send_json(..)`
- React to custom events by implementing our own event handlers as class methods, e.g. `async def react_to_custom_event(self, event):`. Custom events are for handeling messages coming from other consumers or other backend code as opposed to handeling messages from clients.
- Join channel layer groups via `self.channel_layer.group_add(..)` to subscribe clients to additional events (more on that below).

Let's have a look at a simple consumer:

```python
class MyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # We can access the scope object holding connection's information
        # In this case Django Channels will provide
        # authenticated user
        user = self.scope["user"]

        if not user:
            # We don't have to allow the connection to
            # be established.
            await self.close()
            return

        # Join every new connection to the "users" channel group
        # that can be used to later broadcast messages to everyone
        await self.channel_layer.group_add("users", self.channel_name)

    async def disconnect(self, message):
        # Remove the connection from a channel group
        await self.channel_layer.group_discard("users", self.channel_name)

    async def receive_json(self, content, **parameters):
        # Process a message from a client

        # If client sends "Hi", say Hello back
        if "hi" in content:
          await self.send_json({"message": "Hello back!"})

    # Event handlers

    async def react_to_custom_event(self, event):
        # To invoke this event we will need to manually
        # send a message to channel layer with this event name
        ...
```

### CoreConsumer

The main Baserow consumer is `CoreConsumer` (from `backend/src/baserow/ws/consumers.py`). It currently handles all web-frontend connections, all backend events and exchange of all messages between clients and the backend.

### Concurrency and database access

Keep consumer handlers nonblocking. Synchronous database, network, or expensive CPU
work on the event loop delays every connection served by that loop. Channels processes
messages sequentially within each consumer; awaiting a replay or permission check
delays later messages on that socket, while other consumers can continue.

ORM calls must use `run_database_sync` from `baserow.ws.telemetry`, or Channels'
`database_sync_to_async`. In ordinary WebSocket scopes these calls share one
thread-sensitive executor thread per ASGI process. Cold authentication, page
permission checks, and presence-space resolution use this executor. Anonymous and
valid cached-user authentication avoid it. Slow shared operations can still delay
other operations using that thread; adding ASGI workers does not increase the
concurrency within one worker.

`CoreConsumer.dispatch` does not submit database cleanup before every message.
Database-free handshakes and live, presence, and control delivery therefore avoid
waiting behind unrelated shared-thread work. Each ORM adapter cleans connections
before and after its operation on the connection-owning thread, including on error.
Channels also retains its final disconnect cleanup after presence and group teardown.
That final cleanup can wait for the shared thread before the application terminates.
Do not move connection cleanup to an arbitrary thread or create a thread per socket.

Use [WebSocket telemetry](../installation/monitoring.md#websocket-and-realtime-metrics)
to distinguish executor queueing, database execution, and event-loop delays.

## Channel Layer and Channel Groups

In essense, a [channel layer](https://channels.readthedocs.io/en/latest/topics/channel_layers.html) facilitates cross-process communication like the communication between consumers themselves or between consumers and any other backend code that needs to send messages to connected clients. Baserow uses [RedisChannelLayer](https://github.com/django/channels_redis/) for this purpose.

Each consumer has a unique *channel name* (the `self.channel_name` in the example above), and can join arbitrary-named groups, allowing both point-to-point and broadcast messaging.

Currently, `CoreConsumer`s use these channel groups for broadcasts:

- `users` for all connected clients (includes anonymous users)
- page groups representing "table", "view", or "row" pages that have been originally created for people browsing these pages to receive real-time updates
- permission-oriented groups to track consumers that need to listen to permission updates and be able to disconnect from channel groups that they shouldn't be a part of anymore

## Pages and Subscriptions

`CoreConsumer` has a concept of *pages* that a client can subscribe to in order to receive messages targeting specific pages. Clients have to manually request to be subscribed with a special payload. The consumer can then check if the client has the permissions necessary to receive these page updates and if so, add itself to the particular channel group representing the page.

For example, users can subscribe to receive updates to a particular Baserow table. If the request is permitted, the consumer handling the connection will join `table-{id}` channel group and start receiving messages related to the table page with the particular id.

Each page that can be subscribed is implemented as a `PageType` and registered in `page_registry` so it is possible to implement new page types without making changes to the consumer itself. See `backend/src/baserow/ws/registries.py` for details.

## Message Broadcasting

Often we need to notify connected clients about something. For example, clients subscribed to a table page need real-time updates about created or updated rows.

The main method to send a message to all consumers (all clients) in a particular channel group is through `send_message_to_channel_group()` function in `backend/src/baserow/ws/tasks.py`. The `message` parameter should contain the `type` parameter referring to the event handler that will be invoked on each consumer:

```python
from baserow.ws.tasks import send_message_to_channel_group
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

message = {
  "type": "react_to_custom_event",
  # ...event payload
}

group = "table-2"

async_to_sync(send_message_to_channel_group)(channel_layer, group, message)
```

## Front-end

Websocket connections are automatically established for each user, including anonymous users, in the main page layout `web-frontend/modules/core/layouts/app.vue` when the Baserow web-frontend is loaded. Interacting with the backend using websocket connections is abstracted in `RealTimeHandler` class which is available in Vue components under `this.$realtime` property.

Consult client-side documentation in `docs/apis/web-socket-api.md` for implementing webscocket clients for Baserow.

## Web Socket ID

The **web socket id** is a UUID generated once at application boot and stored in the auth store. The client sends it as a query parameter on the WebSocket URL and as a `WebSocketId` HTTP header on REST API requests. The backend uses it to exclude the originating client from the broadcast of its own mutations, so a client never receives an echo of a change it just made.

The ID persists across reconnects within the same page load. A new tab or page refresh generates a fresh UUID.

## Reliability and Event Replay

WebSocket connections drop, and when they do, a client may miss broadcasts sent while it was offline. The reliability layer exists to detect that gap and either fill it (replay the missed events) or flag it (tell the client to refresh).

### Persisted Events

When replay recording is enabled, replayable broadcasts sent through `send_messages_to_channel_group` are **persisted** to the database before being sent. Direct channel-layer messages, including ephemeral presence updates, bypass recording. This creates a replay log keyed by channel group in the `ws_realtime_events` table:

| Field | Type | Purpose |
|---|---|---|
| `id` | `BigAutoField` | Sequential, monotonically increasing. Sent to clients as `_event_id`. |
| `channel_group` | `TextField` | Which channel group this event targeted (e.g., `table-42`, `users`). |
| `payload` | `JSONField` | The full broadcast message including type, user filters, and inner payload. |
| `created_at` | `DateTimeField` | When the event was recorded. Used for retention cleanup. |
| `target_user_ids` | `ArrayField(IntegerField)` | Recipients of users-channel events, derived by the database from the envelope. |
| `all_users` | `BooleanField` | Whether a users-channel event targets every user. Derived by the database. |
| `sentinel_key` | `BinaryField`, nullable | Cleanup marks retained originals with a hash of their exact delivery route. New events leave it null. |

The `id` returned on insert is injected into the payload as `_event_id` before the message is sent.

The table is created as a PostgreSQL `UNLOGGED` table. This skips write-ahead log (WAL) entries, significantly reducing write overhead for high-throughput event recording. The trade-offs are that contents are lost on unclean shutdown (acceptable — events are ephemeral and clients handle the can't-replay path gracefully) and that the table is invisible to streaming replication, so the database router routes all reads of unlogged models to the primary database. Any new unlogged model should follow the same convention.

Recipient selection uses the small `target_user_ids` array and `all_users` flag,
rather than searching every user's individual JSON payload map. A GIN index covers
recipient arrays on the `users` channel, and a partial ID index covers broadcasts
to all users. Page messages use the `(channel_group, id)` index. Full business
payloads are not indexed.

The `ws_realtime_event_targets_before_write` trigger calls
`ws_set_realtime_event_targets()` to derive both columns before insertion
and when `payload` or `channel_group` changes. This also covers old workers that
insert only the original columns during deployment. It reads routing metadata for
users-channel events; page messages need no payload traversal. Live delivery and
replay must continue to agree on recipient selection.

Migration `ws.0002` resets this disposable buffer with `TRUNCATE ... CONTINUE
IDENTITY` before installing the columns, trigger and replacement indexes. It does
not backfill old payloads. The reset and schema changes commit together, with
indexes built while the table is empty and locked. Lock waits are capped at one
second and statements at three seconds, preserving stricter existing limits;
failure rolls the reset back. The event sequence is kept LOGGED and is never
restarted, so pre-reset cursors cannot match unrelated new events.

Apply the migration before deploying new workers. Clients whose cursor was
cleared must refresh their data. Older workers remain write-compatible through
the trigger, but older readers still filter JSON without the previous payload
index and can be slower during rollout. If replay is disabled in production,
leave it disabled until all workers are updated. Reversing this migration also
resets the buffer before restoring its old indexes; neither direction restores
discarded history. These resets affect only realtime replay, not the underlying
user data.

### Last Seen Event ID

During normal delivery, the frontend advances its cursor to the highest `_event_id`
it has processed. The IDs come from a single database sequence. The cursor persists
across workspace and page changes within a page load. During recovery, the client
pins the original cursor and buffers persisted updates until replay completes.

### Replay on Reconnect

When a client reconnects, it re-authenticates, restores its page subscriptions, and
sends a `replay_events` message carrying its last seen event ID as `last_seen_id`.
The server uses that cursor and those subscriptions to decide whether recovery is
possible, with these completed outcomes:

1. **Nothing missed** — Retained payloads and compact history contain no relevant events after the cursor. The original cursor row can already have been compacted; its absence alone does not require a refresh.
2. **Events replayed** — The server fetches the missed events for the client's page channel groups and implicit `users` group, filters out the client's own broadcasts (via its web socket id) and any events not relevant to that user, and re-invokes them through the consumer's handlers in order — exactly as if they had arrived live. The client catches up without a page reload.
3. **Can't replay** — Either too many events were missed (more than `BASEROW_REALTIME_REPLAY_MAX_EVENTS`), a relevant missed event is compacted or older than the configured replay window, history no longer covers the cursor, or the server finds a persisted event it cannot safely re-deliver through a websocket broadcast handler. The server responds with `force_refresh=true` and the client shows a "workspace data is outdated" toast with a refresh action.

Every `replay_events_result` with `force_refresh=false` includes `latest_event_id`, the latest event ID the server can safely acknowledge for that replay decision. If a client connects without a `last_seen_id` (a fresh page load), the server returns the latest persisted event ID as the new baseline because there is nothing to replay. When replay succeeds, `latest_event_id` advances only through events actually replayed, or stays at the supplied cursor when nothing replays. A higher irrelevant ID must not advance the cursor past a relevant INSERT that has not committed yet. If the server responds with `force_refresh=true`, `latest_event_id` is not meaningful and the client should refresh instead.

### Replay resource limits and retries

Replay reads use a separate executor with two active jobs and up to eight FIFO
waiters per ASGI process. A request has a three-second budget for queueing,
connection setup, and execution. PostgreSQL receives a transaction-local statement
timeout using the remaining budget without relaxing a stricter database timeout.
These are internal constants in `backend/src/baserow/ws/replay.py`; they do not
limit event-recording writes. A small result limit alone does not bound how many
irrelevant rows a query may scan.

Queued cancellations remove their waiter. Once a job is submitted, cancellation or
a caller deadline retains its slot until the thread and its connection cleanup
finish. Replay connections close after each job. Configure the database driver's
connection timeout as well: an async deadline cannot stop a blocked synchronous
connection attempt.

For overload, timeouts, and database failures, clients advertising
`supports_retry=true` receive `replay_events_retry` and retry on the same socket
with backoff and jitter. Older clients receive the existing refresh fallback.
Missing history, a relevant expired payload, excessive event gap, or disabled
recording still requires a refresh when recovering missed updates.

The frontend keeps one replay request or retry timer active and holds the original
cursor across retries. It buffers persisted updates up to 1,000 event IDs and an
estimated 5 MiB, then delivers recovered updates in event-ID order with duplicates
removed. Ephemeral presence and control messages bypass this buffer. A fresh
baseline preserves buffered live updates. Buffer overflow, or a disconnect before
the first baseline was established, requires a refresh because recovery can no
longer be verified. An unrecoverable gap stays marked outdated across reconnects.

### Event cleanup and retained sentinels

Full payloads are replayable for `BASEROW_REALTIME_REPLAY_RETENTION_HOURS` hours
(default `24`), independently of JWT lifetime and cleanup progress. Beyond that window, cleanup keeps the newest original event for each
exact audience, originating socket and event type in `ws_realtime_events`. Its
ID, timestamp and payload stay unchanged. This event acts as a sentinel: if it
matches the reconnecting client and its ID is above the client's cursor, the client
missed expired changes and must refresh. An older sentinel alone requires no refresh.

Sentinels remain until a newer original for the same exact route replaces them.
They have no separate age limit. Deleting evidence without a replacement (for
example, through an older cleanup worker) atomically advances a global loss floor: cursors below it must refresh because complete history is no longer
available. This floor occupies one metadata row; there is no separate event-summary
table. Own-socket and excluded-user filters remain identical to live delivery.
The hours setting controls both replay eligibility and the cleanup cutoff. It must
be the same on ASGI and Celery workers. Increasing it cannot recover deleted events:
an already-marked sentinel still requires refresh even inside the enlarged window.

A nullable `sentinel_key` identifies events already retained by cleanup. Ordinary
inserts leave it null; audience hashes are calculated during cleanup. The recipient
columns continue to be derived by the `ws.0002` trigger. A partial unique index
finds the current sentinel for a route; a partial age index finds unprocessed
expired events without repeatedly scanning retained sentinels. Cleanup checks exact
routing equality before combining events, so a hash collision cannot hide changes.
The full payload remains on each sentinel: storage follows distinct audiences and
the size of their last events, rather than every change they made. Exact routes
include socket IDs and recipient sets, so inactive routes can accumulate over time;
the hours setting bounds full replay history, not total sentinel storage.

The periodic Celery task runs every minute, including when recording is disabled,
with a 30-second budget and at most 5,000 candidates per independently committed
batch. Statements use three-second timeouts and 250 ms lock timeouts, preserving stricter settings.
Locked rows wait for a later run; retention bounds replay eligibility but is not a
hard maximum row age. The task uses a nonblocking cleanup lease. A batch that only
retains new sentinels still makes progress, even when it deletes no rows.
The first cleanup run starts compacting existing history. A large backlog is
processed over successive runs; startup never requires compacting the entire table.

Replay reads retained events and the loss floor in one SQL snapshot, avoiding a
race between history deletion and checking its floor. Payload contents of expired
events and marked sentinels are not returned, since either already requires refresh.
The event and metadata tables are UNLOGGED and use the primary database. The event
sequence is LOGGED with its normal `CACHE 1`, preventing ID reuse after a crash.
Missing history state waits for outstanding inserts before establishing a conservative
floor. Migration activation also establishes a floor, so older cursors can require
one refresh. Rollback cannot restore deleted events and leaves the sequence LOGGED.

Compaction migration `ws.0003` installs three additional PostgreSQL functions:

- `ws_realtime_event_routing` extracts and normalizes recipients, exclusions, the
  originating socket and event types. Cleanup hashes this small JSON value instead
  of transferring full expired payloads to Python. It does not run on ordinary inserts.
- `ws_initialize_realtime_history` creates a missing history boundary from the
  durable event sequence, waiting for outstanding inserts first. It is shared by
  migration activation, replay after an UNLOGGED reset, and deletion tracking.
- `ws_record_deleted_realtime_history` runs once per DELETE statement and advances
  the floor atomically with the deletion. Proven duplicate removal temporarily
  bypasses it inside the same transaction; ordinary and legacy DELETEs do not.
  It does not intercept TRUNCATE or arbitrary table replacement.

The PostgreSQL functions are implementation choices: routing could be inline SQL,
initialization could use a Python transaction, and controlled deletion could update
its floor explicitly. The current functions centralize shared logic and preserve
loss tracking for older or direct DELETE statements. Keeping a trustworthy boundary
is necessary when the history supporting numeric replay cursors disappears.

#### Deployment and rollback

Migration `ws.0003` preserves events recorded since `ws.0002`'s buffer reset. It
creates the schema and initializes the floor; it does not compact historical
events. There is no separate activation gate: the updated cleanup task
starts compaction whenever it executes. `BASEROW_REALTIME_REPLAY_MAX_EVENTS=0`
disables recording and replay, but does not pause cleanup.

Pause scheduled cleanup and drain running cleanup tasks before applying `ws.0003`.
Pausing Beat does not remove queued or reserved task messages, so drain or prevent
those tasks from executing.
Update **all ASGI readers before starting any updated Celery worker** that could
consume a cleanup task, then finish the Celery rollout. Submit one cleanup task,
check its metrics and database load, and resume the one-minute schedule. WebSocket
traffic and event recording can continue during this sequence.
Older ASGI readers do not recognize the replay window or loss floor and could
mistake retained sentinels for complete replay history; do not run the new cleanup
while those readers remain. A legacy DELETE advances the floor for new readers,
so accidental older cleanup cannot silently erase their evidence.

The migration adds a nullable column without rewriting event payloads and builds
its indexes concurrently. The builds still need disk and I/O headroom to scan the
existing table and can take much longer than the short schema-lock timeout. The
routing function is only installed during migration; historical events are hashed,
marked and deleted by cleanup. Brief schema locks are bounded; an interrupted
migration can be retried. For rollback, pause and drain cleanup again and disable replay
with the existing `BASEROW_REALTIME_REPLAY_MAX_EVENTS=0` before returning traffic to
older readers. Reversing the migration cannot restore deleted events. Before
re-enabling replay, clear recorded replay history while recording remains disabled
so retained cursor IDs cannot falsely establish a complete pre-rollback history.

The existing `(created_at, id)` index remains available for age diagnostics and
compatibility with earlier cleanup workers. Recipient indexes remain restricted
to the shared `users` channel; page events retain the
`(channel_group, id)` index. Cleanup makes storage reusable through PostgreSQL
vacuum; it does not normally shrink allocated files. Monitor recording rate,
committed cleanup progress, and vacuum activity together; see
[Monitoring](../installation/monitoring.md#websocket-and-realtime-metrics).
See PostgreSQL's [partial-index](https://www.postgresql.org/docs/18/indexes-partial.html),
[concurrent-index](https://www.postgresql.org/docs/18/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)
and [unlogged-table](https://www.postgresql.org/docs/18/sql-createtable.html) documentation.

The replay table uses the same autovacuum thresholds as the pending search values table:
analyze threshold `2000` with scale factor `0.002`, and both update/delete and
insert-triggered vacuum thresholds `5000` with scale factor `0.01`. For example,
autoanalyze becomes eligible after approximately `2000 + 0.002 × estimated rows`
changes. These settings affect eligibility; background-worker scheduling and
available I/O still determine when maintenance runs. The migration does not run
an immediate `ANALYZE`.

### Configuration

| Setting | Default | Purpose |
|---|---|---|
| `BASEROW_REALTIME_REPLAY_RETENTION_HOURS` | 24 | Positive integer hours of full replay history. Older events compact into the latest original per exact audience; sentinels remain until replaced. Increasing the window cannot restore compacted history. |
| `BASEROW_REALTIME_REPLAY_MAX_EVENTS` | 200 | Maximum number of missed events the server will replay. Beyond this, the client is told to refresh. Set to `0` to disable event recording and replay; retention cleanup continues. Clients learn replay availability during authentication and use refresh when missed events cannot be recovered. |

See [configuration.md](../installation/configuration.md) for the full settings reference.
