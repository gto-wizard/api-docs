# Task options

You set these options when you open a task. They apply to every hand of the task.

## Effort

`effort` selects how hard the solver works on each decision.

| `effort` | Name | Use |
| --- | --- | --- |
| 0 | Fast | Lower precision, shorter run. |
| 1 | Standard | The default. |

Any other value answers 400 `GTO_SCORE_EFFORT_NOT_SUPPORTED`. GTO Wizard adds higher levels later.

## Content type

`content_type` declares the one kind of hand that the task scores. Every hand of the upload must
match it.

| `content_type` | The hands it scores |
| --- | --- |
| `nlhe.cash.1` | No-Limit Hold'em cash. The default. |
| `plo.cash.1` | 4-card Pot-Limit Omaha cash. |

Any other value answers 422. Upload **one kind of hand per task**. To score Hold'em cash and PLO
cash, open one task for each.

The `.1` suffix is the version of the scoring of that content. A later change to how GTO Score
scores a kind of hand arrives as a new value, so the contract you integrated against does not change
under you.

A hand that does not match the declaration is not an error for the whole file. It comes back with
`billable: false` and a reject reason: `VARIANT_NOT_SUPPORTED` for the wrong variant,
`FORMAT_NOT_SUPPORTED` or `TOURNAMENT_NOT_SUPPORTED` for the wrong format.

**PLO and your poker room.** GTO Score reads the variant of a hand from the export of the poker room.
Some rooms do not write the variant in the export, so GTO Score refuses their PLO hands. Ask your GTO
Wizard representative whether your room's export carries the variant before you open a
`plo.cash.1` task.

## Scope

`scope` selects how many seats of each hand GTO Score scores.

| `scope` | Scores | Billable units per hand |
| --- | --- | --- |
| `player` | One seat: the nickname in `player`, else the hero seat of the hand. The default. | 1 |
| `table` | Every seat that shows its hole cards. | One per scored seat |

**A `table` scope costs one solve per seat.** Each seat is a full, separate solve of the hand from
that seat's point of view. A six-handed hand whose six seats all show their cards costs six billable
units and takes about six times as long. Ask your GTO Wizard representative for the price of a
`table` scope before you send one.

- `player` must be empty for a `table` scope. A request that names a seat and asks for `table`
  answers 422.
- A hand where only one seat shows its cards costs one unit, the same as a `player` scope.

Each scored seat gets its own row in the hands list and its own `hand_id`. The players table holds
one row per scored nickname.

## Metrics

`metrics` states what a score prices, and so how many billable units each hand costs.

| `metric` | Meaning | Applies to |
| --- | --- | --- |
| `CHIP_EV` | The decision is priced in chips. | Every hand. |
| `ICM` | The decision is priced in tournament equity, through the Independent Chip Model. | A tournament hand only. |

**Each entry of `metrics` is one billable unit per hand.** A hand priced both ways costs two units.

`metrics` is refused with 422 when it names a value that is not `CHIP_EV` or `ICM`. A value that
repeats counts once.

| `metrics` | Cash hand | Tournament hand with a sidecar record | Tournament hand without one |
| --- | --- | --- | --- |
| `[]` (the default) | one `CHIP_EV` unit | one `ICM` unit | one `CHIP_EV` unit |
| `["CHIP_EV"]` | one `CHIP_EV` unit | one `CHIP_EV` unit | one `CHIP_EV` unit |
| `["ICM"]` | no unit, no row, no bill | one `ICM` unit | one refused `ICM` unit, not billed |
| `["CHIP_EV", "ICM"]` | one `CHIP_EV` unit | one of each | `CHIP_EV` scored, `ICM` refused |

A tournament hand needs a sidecar file whatever `metrics` says. Without one, the hand is refused with
`TOURNAMENT_NOT_SUPPORTED`.

`ev_loss` and `total_ev_loss` stay in big blinds on both metrics. On an `ICM` unit they are the EV
lost after the model priced the stacks, not a chip count.

The players table of `GET /v4/fair-play/gto-score/{task_id}/` groups the **first** unit of each
hand, which is the `CHIP_EV` unit when the task prices a hand both ways. Read the per-hand and
per-action calls for the ICM scores of a two-metric task.
