# Tournament inputs (preview)

> **Preview. This format can change.** Tell your GTO Wizard representative if a field does not match
> what your export can produce, before you build against it.

A hand history names the tournament, the level and the stacks at the table. It does not name the
payout structure, the players still in the tournament, the chips they hold or the bounty on each
seat. The Independent Chip Model (ICM) needs all of them. So you send them beside the hands, in a
**sidecar file** that you declare at `sign` with `"kind": "TOURNAMENT_INPUTS"`.

## The file format

The file is **JSON Lines**: one JSON object per line, UTF-8. A blank line is skipped. A name that ends
with `.gz` is one gzip member. One task can declare more than one sidecar file, and their records
join into one set.

Two record types share the file. `type` selects the record, and `version` is `1`.

```json
{"type":"tournament","version":1,"id":"9160000001","structure":{...}}
{"type":"hand","version":1,"id":"910000000002","state":{...}}
```

## The `tournament` record

`id` is the tournament number, exactly as the room wrote it in the hand header. `structure` holds
what stays the same for the whole tournament.

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | no | `NORMAL`, `KO`, `PKO` or `TKO`. `NORMAL` by default. |
| `payout_levels` | yes | Every paid place. One entry per rank. |
| `bounty_instant_percentage` | no | The part of a bounty that the eliminating player takes at once. A PKO normally uses `0.5`. Needs a `KO`, `PKO` or `TKO` type. |
| `currency` | no | Three letters. It applies to every prize and bounty. |
| `total_entrants` | no | Players who entered the tournament. |

Each `payout_levels` entry holds `rank` (1 is the winner) and `prize` (without any bounty). The ranks
start at 1 with no gap, and a lower place cannot pay more than a higher one.

```json
{"type":"tournament","version":1,"id":"9160000001","structure":{
  "type":"PKO","bounty_instant_percentage":0.5,"currency":"USD","total_entrants":500,
  "payout_levels":[{"rank":1,"prize":500},{"rank":2,"prize":300},{"rank":3,"prize":200}]}}
```

## The `hand` record

`id` is the hand number, exactly as the room wrote it. It joins the record to the uploaded hand.
`state` holds what changed by the time that hand was played.

| Field | Required | Meaning |
| --- | --- | --- |
| `tournament` | yes | The `id` of a `tournament` record in the same task. |
| `players_remaining` | yes | Players still in the tournament, at every table together. 2 or more. |
| `stacks` | one of the two | The stack of every remaining player, in big blinds of this hand. |
| `average_stack` | one of the two | The mean stack of the remaining players, in big blinds of this hand. |
| `stacks_distribution_type` | no | Shape of the sample chip distribution. `LogNormal` by default. |
| `lognormal_deviation` | no | Deviation of the LogNormal distribution. |
| `bounties` | no | Total bounty on each seat of this table, by nickname. |
| `average_bounty` | no | Mean bounty left on a player away from this table. |

**Give `stacks` or `average_stack`, never both.** `stacks` must hold exactly `players_remaining`
values, each more than 0. With `average_stack`, the scoring builds a sample distribution of
`players_remaining` stacks around that mean.

```json
{"type":"hand","version":1,"id":"910000000002","state":{
  "tournament":"9160000001","players_remaining":120,"average_stack":40,
  "bounties":{"alpha":25,"bravo":12.5},"average_bounty":18}}
```

## Limits

| Cap | Value |
| --- | --- |
| `players_remaining`, `stacks` length, `payout_levels` length | 4096 |
| Tournament id and hand id length | 128 characters |
| All sidecar files of one task together, decompressed | 268,435,456 bytes (256 MiB) |

A sidecar file counts against the file count and the size caps of the task, like a hand file. A
`hand` record with `average_stack` is about 140 bytes, so the 500,000-hand cap applies first. A full
`stacks` list of 180 players is about 1,750 bytes, which allows about 150,000 hands per task.

## What the API refuses

The sidecar files are read once, after `complete`. A file that does not match the format ends the
task as `FAILURE`, and `error_message` names the file and the line. A task that declares a sidecar
file and no hand file answers 400 at `complete`.
