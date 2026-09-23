# Limits

Your application has a record limit for each month. GTO Wizard agrees it with you.

Every read of a task reports two numbers:

- `limit` — how many records your application can send in a month.
- `quota` — how many it sent this month.

## When the limit runs out inside a file

A batch stops when the limit runs out. The task still reaches `SUCCESS`, and the
result holds the rows it reached.

`result.last_processed_id` names the last row the work read. It is the `id` from
your own file. Send the rest of the file after the limit resets, and start from
the row after that one.

A send call that arrives with no limit left answers 400 with
`Your monthly upload limit has been reached.`

## The other limits

| Limit | Value |
| --- | --- |
| Rows in one file | 100000 |
| Life of a result link | 24 hours |
| Life of an access token | 10 hours |
| Boards from the player call | 100 by default, 500 at most |

## Watching your use

Read any finished task to see `limit` and `quota`. Both count the calendar month.
Plan a large export around what is left.
