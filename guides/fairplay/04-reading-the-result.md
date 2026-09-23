# Reading the result

Ask for the task until it finishes.

```shell
curl 'https://api.gtowizard.com/v1/poker/fair-play/<task id>/' \
  --header 'Authorization: Bearer <access token>'
```

## The four states

| `status` | What it means |
| --- | --- |
| `PENDING` | The task waits its turn. |
| `STARTED` | The work runs. |
| `SUCCESS` | The result is ready. The answer holds `result`. |
| `FAILURE` | The work stopped. `error_message` says why. |

Ask again every few seconds while the status is `PENDING` or `STARTED`. A large
file takes minutes.

## The result

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "SUCCESS",
  "variant": "NLHOLDEM",
  "limit": 100000,
  "quota": 15000,
  "error_message": null,
  "result": {
    "file_url": "<a link to the result file>",
    "expires_in": 86400,
    "last_processed_id": "hand-000123"
  }
}
```

`file_url` is a link to the result CSV. It lives for 24 hours. Download the file
inside that time. After it expires, ask for the task again and you get a new link.
The file itself does not expire.

## The result file

One row is one solution lookup that matched one of your hands. A hand with no
match has no row. A hand can have more than one row.

The columns, separated by semicolons:

| Column | What it holds |
| --- | --- |
| `Site ID` | Your own `id` for the hand, from the file you sent. |
| `Board` | The board that the player opened in GTO Wizard. |
| `Timestamp` | When the player opened it. |
| `Game Format` | The format of the solution, for example `Cash`. `CUSTOM` means the player used a tree of their own. |
| `Stack Depth` | The stack depth of the solution, in big blinds. |
| `Stacks` | The stack of every seat, joined by `-`. |
| `Pot Size` | The pot at that point of the solution. |
| `OOP` | The seats out of position. |
| `IP` | The seat in position. |
| `Action Sequence` | The action line the player looked up. |
| `Solution` | The solution the player opened. |
| `User ID` | The GTO Wizard account that made the lookup. |

`User ID` is the key to the next step. With it you can read every recent board
that same account opened, and see whether this one match is a habit.

## When the work fails

`FAILURE` puts the cause in `error_message`. Correct the file and send it again.
The same answer reports `limit` and `quota`, so you can see what the attempt used.
