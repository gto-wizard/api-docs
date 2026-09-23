# Authentication

FairPlay uses OAuth2 with the client-credentials grant.

Your application holds a client id and a client secret. You exchange them for an
access token. The token opens every other call. Keep both the secret and the token
private.

## Get a token

Join the client id and the client secret with a colon, encode the result as
Base64, and send it as HTTP Basic.

```shell
curl -X POST 'https://api.gtowizard.com/v1/account/oauth/token/' \
  --header 'Authorization: Basic <base64 of client_id:client_secret>' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials'
```

The answer:

```json
{
  "access_token": "<access token>",
  "expires_in": 36000,
  "token_type": "Bearer",
  "scope": "read"
}
```

The token lives for 10 hours. Ask for a new one when it expires. Do not ask for a
new token before every call.

## Use the token

Every other call takes the token as a bearer token.

```shell
curl 'https://api.gtowizard.com/v1/poker/fair-play/<task id>/' \
  --header 'Authorization: Bearer <access token>'
```

A call with an absent, wrong or expired token answers 401. Get a new token and
send the call again.
