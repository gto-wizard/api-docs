# Files and limits

## What GTO Score reads

GTO Score reads the raw hand-history export of the poker room. Each hand carries its own game type
and its own room in its header. The server checks every hand against the `content_type` of the task.

GTO Score always scores a cash hand of the declared variant. It scores a multi-table tournament (MTT)
hand only for a Hold'em task that also declares a tournament sidecar file. A PLO task refuses a
tournament hand. A heads-up sit-and-go and a spin are always refused.

A hand of another variant or another format is not an error for the whole file. The hand comes back
with `billable: false` and a reject reason.

## One serialization format per task

The reader looks at the first non-empty line of each file and picks one of three formats: `TEXT`,
`JSON` or `XML`. Every file of one task must hold the same format. A task whose files mix formats
ends as `FAILURE`, and the message names the file.

Room text formats can share one task. For example, PokerStars text and GGPoker text are both `TEXT`.
An iPoker XML file and a PokerStars text file cannot share a task.

## Compression

A file name that ends with `.gz` is read as one gzip member. Hand-history text compresses about 11
times.

A file that ends with `.gz` and is not readable gzip ends the task as `FAILURE`.

## Size caps

| Cap | Value | Where it applies |
| --- | --- | --- |
| One file | 1,073,741,824 bytes (1 GiB) | `sign` on the declared size, `complete` on the stored size |
| One task | 2,147,483,648 bytes (2 GiB) | `sign` on the declared sizes, `complete` on the stored sizes, and on the decompressed stream |
| Files per task | 50 | Counted over every `sign` call together |
| Hands per task | 500,000 | Counted after the split |

`sign` adds up the sizes of every `sign` call of the task, so it refuses a task over the total before
any presigned URL exists. `complete` checks the same total again, from the real stored sizes.

A declared size over a cap answers 400 `UPLOAD_TOO_LARGE`, and the task keeps the files it already
declared. A stored size over a cap answers the same at `complete`. A task over the hand cap or over
the decompressed byte cap ends as `FAILURE`, because GTO Score knows both only after the split.

The 2 GiB cap applies to the **decompressed** stream. A gzip file can expand about 1000 times, so a
small upload can still pass the cap.
