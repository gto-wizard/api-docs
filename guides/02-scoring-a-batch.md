# Scoring a batch

You write the hand files straight to storage. The API never holds the file. One batch takes four
steps, then a poll:

```
1. POST /v4/fair-play/gto-score/                 -> 201 {task_id}
2. POST /v4/fair-play/gto-score/{id}/sign/       -> 200 presigned PUT URLs
3. PUT  <each presigned URL>                     -> 200 from storage
4. POST /v4/fair-play/gto-score/{id}/complete/   -> 202, the scoring starts
   GET  /v4/fair-play/gto-score/{id}/            -> poll until SUCCESS or FAILURE
```

## Step 1: open the task

```http
POST /v4/fair-play/gto-score/

{ "player": "Villain42", "effort": 1, "content_type": "nlhe.cash.1", "scope": "player", "metrics": ["CHIP_EV"] }
```

Every field is optional. The **Task options** guide explains `effort`, `content_type`, `scope` and
`metrics`.

- `player` is the nickname of the one seat to score. An empty `player` scores the hero seat of each
  hand. A hand with no single hero is rejected with `NO_SINGLE_HERO`.

The answer is 201 with `task_id`, `status`, `effort`, `player`, `content_type`, `scope` and
`metrics`. The status is `PENDING`.

**One task of an application runs at a time.** While a task is `PENDING` or `STARTED`, a second
`POST` answers 409 `GTO_SCORE_TASK_IN_FLIGHT`, and the message names the task that holds the slot.
Wait for that task to reach `SUCCESS` or `FAILURE`, then open the next one.

## Step 2: presign the files

```http
POST /v4/fair-play/gto-score/{task_id}/sign/

{ "files": [ { "name": "2026-09-hands.txt.gz", "size_bytes": 34012994, "kind": "HANDS" } ] }
```

`size_bytes` is the byte count of the body that you will send. The API signs the length into the URL,
so a body of a different length fails at storage.

`kind` says what the file holds. `HANDS`, the default, is a hand-history export.
`TOURNAMENT_INPUTS` is a tournament sidecar file. See the **Tournament inputs** guide.

The answer holds one `presigned_puts` entry per declared file, in the order of the request:

| Field | Meaning |
| --- | --- |
| `name` | Echo of the declared name. |
| `key` | The storage key that the URL writes. |
| `url` | The presigned PUT URL. |
| `required_headers` | Headers that the PUT must carry unchanged. |

`expires_at` is the time that every URL of the answer stops working. The lifetime is one hour.

Call `sign` again to add more files to the same task. Every file of one task needs its own name.

**File names.** A name starts with a letter or a digit. After that it can hold letters, digits and
`. _ -`. A name cannot hold a path separator and cannot hold `..`. The limit is 255 characters.

## Step 3: write the files

Send each file with a PUT to its URL. Send every header of `required_headers` unchanged:

```http
PUT <url>
Content-Type: application/octet-stream
Content-Length: <size_bytes>

<the file bytes>
```

Storage refuses the PUT when the length or the content type is different from the signed value.

## Step 4: complete the upload

```http
POST /v4/fair-play/gto-score/{task_id}/complete/
```

The API reads the size of every stored file, checks the size caps again against the real sizes, then
starts the scoring. The answer is 202 with the task id and the status.

The call is safe to repeat. A task whose upload is already complete answers 202 again and starts no
second job.

`complete` answers 404 `UPLOAD_OBJECT_MISSING` when a declared file is not in storage. Send the
missing PUT, then call `complete` again.

## Polling

Poll `GET /v4/fair-play/gto-score/{task_id}/` until `status` is `SUCCESS` or `FAILURE`. The players
table is empty until the task ends. On `FAILURE`, read `error_message`.

A batch of 500,000 hands takes hours. Poll every few minutes, not every second.

GTO Wizard can also call your endpoint when a task ends. See the **Completion webhook** guide. The
webhook does not replace the poll: it tells you when to read, and the poll always gives the state of
the task.
