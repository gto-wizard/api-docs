# Authentication

You upload the hands, wait for the scoring, then read the scores per player, per hand and per
action. All calls go to `https://business.gtowizard.com`. Every path starts with `/v4/`.

## Get your credentials

GTO Score authenticates an **application**, not a user.

1. Your GTO Wizard representative creates an application for you and turns GTO Score on for it.
2. You receive a `client_id` and a `client_secret` through a one-time secret link.
3. Keep the `client_secret` on your server. Do not put it in a browser, a mobile app or a
   repository.

GTO Wizard stores only a hash of the secret, so nobody can send it to you again. If you lose it, ask
for a new one.

## Get an access token

Send the client-credentials request:

```http
POST https://business.gtowizard.com/v4/accounts/oauth2/token/
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "<client id>",
  "client_secret": "<client secret>"
}
```

```shell
curl -X POST https://business.gtowizard.com/v4/accounts/oauth2/token/ \
  -H 'Content-Type: application/json' \
  -d '{"grant_type": "client_credentials", "client_id": "<client id>", "client_secret": "<client secret>"}'
```

The endpoint also accepts `application/x-www-form-urlencoded`, which is what a standard OAuth2 client
library sends.

The answer holds `access_token`, `token_type` and `expires_in` (seconds). Ask for a new token before
`expires_in` runs out.

GTO Score needs no special OAuth scope. The default scope of an application token is sufficient.

## Send the token

Send the token in the `Authorization` header of every GTO Score call:

```http
Authorization: Bearer <access token>
```

On this site, type the token into the **Authentication** box. Every code sample then carries it. The
token stays in your browser. This site sends no request to the API and to no other server.

## Authentication failures

| Answer | Meaning |
| --- | --- |
| 401 | The token is absent, expired or unknown. Get a new token. |
| 403 `GTO_SCORE_NOT_ENABLED` | The token is good, and GTO Score is off for this application. Contact your GTO Wizard representative. |
