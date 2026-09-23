# Sending a batch

You send the hands as a CSV file. The format is the same for every poker room.

## The file

The first line holds the column names. Four columns are necessary. A semicolon or
a comma can separate them.

| Column | What it holds |
| --- | --- |
| `id` | Your own reference for the hand. FairPlay echoes it back and never reads it. |
| `board` | The board cards, joined with no separator, for example `6hjhtd`. |
| `board_dealt_at` | When the board was dealt. |
| `hand_finished_at` | When the hand finished. |

Write both times in the ISO 8601 form, with the offset from UTC:
`2026-04-12T22:03:17+00:00`.

The board can be a flop, a turn or a river. Send the board as the players saw it
at the point you want checked.

```csv
id;board;board_dealt_at;hand_finished_at
hand-000123;6hjhtd;2026-04-12T22:03:17+00:00;2026-04-12T22:03:54+00:00
hand-000124;8c4d9s;2026-04-12T22:02:58+00:00;2026-04-12T22:03:54+00:00
hand-000125;QsTs7h7s3h;2026-04-12T22:30:34+00:00;2026-04-12T22:40:34+00:00
```

A file holds at most 100000 rows. Split a larger export.

The pair of times is the window FairPlay searches. Keep it tight. A window wider
than the hand brings in lookups that the player could have made after the hand,
which are not evidence of anything.

## Send it

```shell
curl -X POST 'https://api.gtowizard.com/v1/poker/fair-play/' \
  --header 'Authorization: Bearer <access token>' \
  --form 'file=@hands.csv'
```

For Pot-Limit Omaha, add the variant. It applies to every row of the file.

```shell
curl -X POST 'https://api.gtowizard.com/v1/poker/fair-play/' \
  --header 'Authorization: Bearer <access token>' \
  --form 'file=@hands.csv' \
  --form 'variant=PLO4'
```

The answer holds the task id:

```json
{
  "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "state": "PENDING",
  "variant": "NLHOLDEM"
}
```

**Keep the task id.** It is the only way to reach the result.

## When the call refuses the file

The answer is 400 and the body names the cause in one sentence.

| The body says | What to do |
| --- | --- |
| `Your monthly upload limit has been reached.` | Wait for the limit to reset, or agree a larger one. |
| `Could not parse CSV headers.` | Give the file a header line. |
| `Missing required CSV headers: ...` | Add the columns it names. |
| `File has too many rows ...` | Split the file. |
| `Invalid variant: ...` | Send `NLHOLDEM` or `PLO4`. |
