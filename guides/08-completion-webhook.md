# Completion webhook

GTO Wizard can POST to an endpoint of yours when a task reaches `SUCCESS` or `FAILURE`. The call
carries the task id and the status. You then read the results over the API as usual.

The webhook is **optional**. A call that never arrives does not change the task. Keep the poll as the
source of the state, and use the webhook to know when to poll.

## Switching it on

Give your GTO Wizard representative one HTTPS URL. GTO Wizard generates a **signing secret** for
your application and gives it to you over a secure channel.

| Rule for the URL | Reason |
| --- | --- |
| The scheme must be `https`. | The signature proves the sender. TLS proves the receiver. |
| The host must resolve to a public address. | A URL into a private network is refused. |
| The URL carries no user name and no password. | The signature is the authentication. |
| A redirect is not followed. | Give the final URL. A `3xx` answer ends the delivery as failed. |

## The request

```http
POST <your callback URL>
Content-Type: application/json
User-Agent: GTOWizard-GtoScore-Webhook/1
X-Gto-Score-Event: gto_score.task.finished
X-Gto-Score-Delivery: 8f14e45f-ea1d-4d3c-9b1c-6b9a7c2f0e11
X-Gto-Score-Signature: t=1758196800,v1=8b4f...c19a

{"status":"SUCCESS","task_id":"8f14e45f-ea1d-4d3c-9b1c-6b9a7c2f0e11"}
```

The body holds `task_id` and `status` and nothing else: no hand, no nickname, no score. Answer with
any `2xx` status. GTO Wizard reads the status code only.

## Verifying the signature

`X-Gto-Score-Signature` holds `t`, the time of the attempt in epoch seconds, and `v1`, the signature
in lowercase hexadecimal. The signature is `HMAC-SHA256`, keyed with your secret, over:

```
<t> + "." + <raw body bytes>
```

```python
import hashlib
import hmac
import time

def is_valid(raw_body: bytes, signature_header: str, secret: str, tolerance_seconds: int = 300) -> bool:
    parts = dict(part.split("=", 1) for part in signature_header.split(","))
    timestamp, signature = parts["t"], parts["v1"]
    if abs(time.time() - int(timestamp)) > tolerance_seconds:
        return False
    expected = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

1. Sign the **raw bytes**. Do not parse and serialize the JSON again.
2. Compare in constant time.
3. Reject an old timestamp. This stops a replay.
4. Answer `4xx` when the check fails.

## Retries

| Answer | What GTO Wizard does |
| --- | --- |
| `2xx` | The delivery is complete. |
| `5xx`, `408`, `425`, `429`, a timeout or a connection failure | Retries with a growing wait. |
| Any other `4xx`, or a `3xx` | Stops and records the delivery as failed. |

There are six attempts in all. The wait doubles from about 30 seconds and never passes 10 minutes, so
the last attempt comes 12 to 25 minutes after the first. One request waits 10 seconds for an answer,
so answer first and do your own work afterwards.

**Use `task_id` as the idempotency key.** A retry arrives with the same `task_id` and `status`. The
`t` value, and so the signature, differs between attempts. Verify each request on its own.

## Rotating the secret

A new secret starts to work at once, and the old one stops at once. Accept both keys during the
change, then drop the old one.
