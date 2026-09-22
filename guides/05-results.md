# Statuses and results

## Task statuses

| `status` | Meaning |
| --- | --- |
| `PENDING` | The task is open. The upload is not complete. |
| `STARTED` | The scoring runs. |
| `SUCCESS` | The scoring ended. Every result is readable. |
| `FAILURE` | The task ended without a full result. `error_message` says why. |

GTO Wizard force-fails a task that stops moving. A `STARTED` task with no progress for 6 hours
becomes `FAILURE`. A `PENDING` task whose upload you did not complete within 24 hours also becomes
`FAILURE`. Both free the in-flight slot of your application, and neither bills a hand.

| Cause | `error_message` |
| --- | --- |
| The files mix serialization formats | `The file <name> holds XML hands, but the task started with TEXT. Upload one format per task.` |
| A `.gz` file is not readable gzip | `The file <name> is not a readable gzip file. Upload it again.` |
| The upload holds more than 500,000 hands | `The file holds more than 500000 hands. Split it into smaller uploads.` |
| The upload expands past 2 GiB | `The uploaded hands expand to more than 2147483648 bytes. Split them into smaller uploads.` |
| The scoring did not finish | `Processing did not finish.` |
| The scoring stopped for 6 hours | `The scoring stopped before it finished. Upload the hands again.` |
| The upload stayed open for 24 hours | `The upload was never completed. Open a new task and upload the hands again.` |

The first four name the file you sent and the cap you passed. Correct the upload and send it again.
The last three mean that GTO Wizard did not finish the task. Send the task again. If it fails a
second time, give the `task_id` to your GTO Wizard representative.

`error_message` never carries hand text or a player nickname.

## Hand outcomes and reject reasons

A hand has three possible outcomes. Read `billable` first, not `reject_reason`.

| Outcome | `billable` | `reject_reason` | Scores | Task counter |
| --- | --- | --- | --- | --- |
| Scored | `true` | empty | set | `hands_scored` |
| Refused | `false` | one of the values below | `null` | `hands_rejected` |
| Accepted, not scored | `false` | **empty** | `null` | `hands_unscored` |

**An empty `reject_reason` does not mean that the hand was scored.** In the third row, GTO Score
accepted the hand and the solver returned no usable score. `billable` is the field that separates
the two.

| `reject_reason` | Meaning |
| --- | --- |
| `PARSE_FAILED` | The parser could not read the hand, or the hand has no hand number. |
| `VARIANT_NOT_SUPPORTED` | The hand is not the variant that the task declared in `content_type`. |
| `FORMAT_NOT_SUPPORTED` | The hand is not a cash hand. |
| `TOURNAMENT_NOT_SUPPORTED` | The hand is a tournament, a heads-up sit-and-go or a spin. |
| `SEAT_NOT_IN_HAND` | The scored nickname does not sit in this hand. |
| `SEAT_WITHOUT_HOLE_CARDS` | The scored seat shows no hole cards. Under a `table` scope, no seat of the hand does. |
| `NO_SINGLE_HERO` | `player` is empty and the hand names no single hero. |
| `NO_HERO_ACTION` | The scored seat took no action in the hand. |
| `TOURNAMENT_INPUTS_MISSING` | The task asked for `ICM` on a tournament hand, and no sidecar `hand` record names that hand. |
| `TOURNAMENT_INPUTS_DISAGREE` | The sidecar record and the hand cannot both be true, for example fewer players left than seats at the table. |
| `TOO_MANY_PLAYERS` | The hand seats more players than the solver tree of its shape holds. |
| `SHAPE_NOT_SUPPORTED` | The shape of the hand has no solver tree. |
| `SOLVER_REFUSED` | The solver accepted the shape and refused the line. |
| `SOLVER_FAILED` | The solve failed. |

## The score scale

The API returns a GTO score as a decimal fraction in **`[0.00, 1.00]`**, rounded to two decimal
places. `1.00` means the best action at every scored decision. `null` means that nothing was scored.

| Field | Meaning |
| --- | --- |
| `gto_score` on a hand or a street | The score of the **worst** action of the seat. |
| `avg_gto_score` on a hand | The mean score of the actions of the seat in that hand. |
| `avg_gto_score` on a player | The mean score of the hands of that player. |

`ev_loss` and `total_ev_loss` are in big blinds and are not on this scale. `solver_frequency` is a
frequency in `[0, 1]`.

## Reading the results

**The task and the players table.** `GET /v4/fair-play/gto-score/{task_id}/` returns the state of the
task and one page of the players table. Counters: `hands_total`, `hands_scored`, `hands_unscored`,
`hands_rejected` and `hands_billable`. `billable_units` splits `hands_billable` per metric.
`last_processed_id` is the hand number of the last hand the scoring reached; use it to watch a long
task move. Paging: `limit` (default 100, maximum 1000), `offset` and `total`. `order_by` picks the
column, and a leading `-` orders descending.

**The hands.** `GET /v4/fair-play/gto-score/{task_id}/hands/` returns one page of hands, ordered by
the time the hand was played. The `player` query parameter keeps only the hands of one nickname.
`hand_correctness` is the correctness of the worst action of the seat: `BEST_MOVE`, `CORRECT_MOVE`,
`INACCURACY`, `WRONG_MOVE`, `BLUNDER` or `UNSOLVED`.

**One hand in full.** `GET /v4/fair-play/gto-score/{task_id}/hands/{hand_id}/` adds `streets`, keyed
`PREFLOP`, `FLOP`, `TURN` and `RIVER`. Each street holds its `gto_score` and the `actions` of the
seat, with `ev_loss`, `solver_frequency` and `best_action` at each decision.

## Bulk export

The paged calls return JSON, one page at a time. The export returns every scored action of a task as
**one file**, in `csv` or `jsonl`.

```
1. POST /v4/fair-play/gto-score/{id}/exports/              -> 202 {export_id, status: PENDING}
2. GET  /v4/fair-play/gto-score/{id}/exports/{export_id}/  -> poll until SUCCESS
3. GET  <file.url>                                         -> the file
```

- The task must have finished. A `PENDING` or `STARTED` task answers 409 `CONFLICT`. A task that
  ended as `FAILURE` can be exported: it carries the hands scored before it stopped.
- One export of a task runs at a time. A second POST answers 409 `CONFLICT`.
- `columns` picks the columns and their order. An empty list writes every column.
- `file.url` is a signed URL that works without your token and stops working at `file.expires_at`,
  one hour later. Read the export again for a new URL. The file does not change.
- The file holds **one row per scored action**. A hand that GTO Score did not solve writes no row.
- The CSV writes `gto_score` with two decimals (`0.10`). The JSON Lines file writes a JSON number
  (`0.1`). Both are the same value. A CSV cell that a spreadsheet would read as a formula starts
  with `'`.
