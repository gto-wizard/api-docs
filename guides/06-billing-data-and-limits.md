# Billing, data and rate limits

## Billing

GTO Score bills the **units** that it scores.

- One scored hand is one unit of its metric. A hand priced both ways is two units.
- `billable` is `true` only for a unit that the solver scored.
- A unit with a `reject_reason` is not billed.
- A unit with an empty `reject_reason` and `billable: false` is also free.
- **A hand that the solver cannot handle is free.**
- `hands_billable` on the task counts the billable units over every metric. `billable_units` splits
  it per metric. GTO Score writes `hands_billable` when the task ends.

A contracted application has no quota and no monthly limit.

## Sandbox

A sandbox application lets you build and test an integration before your contract starts. It works
exactly like a contracted application, with one difference: a **monthly hand limit**.

- The limit counts the billable hands of the calendar month.
- When the limit is spent, opening a task answers 403 `GTO_SCORE_MONTHLY_LIMIT_REACHED`. The message
  names the limit and the hands already sent.
- An upload that would pass the limit ends the task as `FAILURE` before the solver runs. **Nothing is
  billed.** The check counts every hand of the upload, including the hands GTO Score would reject.
- The limit refills at the start of the next month.

## Purge: GTO Wizard keeps no hands

The hands are deleted as soon as the batch is scored. The scores stay.

- Deleted: the uploaded files, the parsed hands, the hole cards and the boards.
- Kept: the per-player, per-hand and per-action scores, keyed by the hand number that the poker room
  wrote.

The hand detail call therefore returns no hole cards, no board and no hand text at any time. It
returns the actions of the scored seat with their scores.

`hands_purged_at` on the task is the time of the delete. It is `null` until the purge runs. There is
no retention setting and no DELETE endpoint. The export file carries scores, not hands, so the purge
does not delete it.

## Rate limits

The limits apply per application. Reads and writes have separate counters, so paging a large result
cannot stop you from opening the next batch.

| Calls | Limit |
| --- | --- |
| The four POST calls | 60 per hour |
| The four GET calls | 6000 per hour |

One batch uses three writes: open, sign, complete. An export uses a fourth. 60 writes an hour is 15
batches with one export each.

A request over the limit answers 429. The body holds `request_limit` and `time_period_in_seconds`,
and the `Retry-After` header gives the seconds to wait.

## Error codes

Every error answer carries a `code` and a `detail`.

| HTTP | `code` | Meaning |
| --- | --- | --- |
| 400 | `GTO_SCORE_EFFORT_NOT_SUPPORTED` | `effort` is not an offered level. |
| 400 | `UPLOAD_TOO_LARGE` | A file or the task is over a size cap. |
| 400 | `VALIDATION_ERROR` | A file name is not valid, a name repeats, a size is not positive, the task would hold more than 50 files, or `complete` ran before any `sign`. |
| 401 | — | The token is absent, expired or unknown. |
| 403 | `GTO_SCORE_NOT_ENABLED` | GTO Score is off for this application. |
| 403 | `GTO_SCORE_MONTHLY_LIMIT_REACHED` | A sandbox application spent its monthly hand limit. |
| 404 | `NOT_FOUND` | The task, the hand or the export does not exist, or it belongs to another application. |
| 404 | `UPLOAD_OBJECT_MISSING` | A declared file is not in storage. |
| 409 | `CONFLICT` | The task is not `PENDING`, its files changed during `complete`, the task of an export has not finished, or the task already holds a running export. |
| 409 | `GTO_SCORE_TASK_IN_FLIGHT` | The application already holds a task that has not finished. |
| 422 | — | The request body does not match the schema. |
| 429 | — | The application spent its budget for the hour. |

A task of another application answers 404, not 403. You cannot learn that another partner's task
exists.
