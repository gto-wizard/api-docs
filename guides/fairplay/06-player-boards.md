# The boards of a player

One match tells you little. A pattern tells you more.

Every row of a result file names the GTO Wizard account that made the lookup, in
the `User ID` column. With that id you can read the most recent boards the same
account opened, newest first.

```shell
curl 'https://api.gtowizard.com/v1/poker/fair-play/users/<user id>/boards/' \
  --header 'Authorization: Bearer <access token>'
```

The answer is JSON, and each entry holds the same facts as a row of a result file:

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "acc_000000000",
    "created_at": "2026-03-21T13:58:06.155879+01:00",
    "original_board": "AsKsQs",
    "format": "Cash",
    "gametype_name": "Cash6m500zBasic",
    "depth": "100.000",
    "stacks": "100.000-100.000-100.000-100.000-100.000-100.000",
    "pot": "5.500",
    "ip_position": "BTN",
    "oop_positions": ["BB"],
    "actions": "F-F-F-R2.5-F-C|X"
  }
]
```

## Narrow the answer

`from` keeps only the lookups after a moment. Write the time with its offset, and
encode it for the URL.

```shell
curl -G 'https://api.gtowizard.com/v1/poker/fair-play/users/<user id>/boards/' \
  --data-urlencode 'from=2026-03-22 20:34:52+00:00' \
  --header 'Authorization: Bearer <access token>'
```

`limit` sets how many boards come back. The default is 100 and the most is 500.

## What this shows

These are the boards one account looked up, with the time of each lookup. Compare
them with the hands that account played in your room. A few matches can be
chance. A run of them, hand after hand, is not.
