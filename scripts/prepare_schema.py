#!/usr/bin/env python3
"""Turn the backend's business OpenAPI document into the public one, and guard
every OpenAPI document this site publishes.

The site holds one document per product: GTO Score, made by this script from the
backend schema, and FairPlay, written by hand because the backend generates no
schema for that API. `--check` reads both, so a hand-written document gets the
same reading as a generated one.

This repository is public, so every schema that enters it passes through this
script. The script changes three things and refuses the rest:

1. It replaces `info.description` with the partner text below.
2. It declares the real wire format of the credential, an HTTP bearer token,
   so the reference shows a token box and writes the token into every sample.
3. It keeps only the error codes that a GTO Score call can answer.

Then it checks the result and exits non-zero on any finding. A failed check
means a human must look before the schema goes public.

Usage:
    prepare_schema.py <source.json> <output.json>   write the public schema
    prepare_schema.py --check <file.json> [...]      check published schemas
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SOURCE_SCHEME = "GtoScoreApplicationAuthentication"
PUBLIC_SCHEME = "BearerAuth"
BASIC_SCHEME = "BasicAuth"

# The site holds one document per product. `prepare` only makes the GTO Score one,
# from the backend schema. The FairPlay document is written by hand, because the
# backend generates no schema for that API. `check` guards both, so a hand-written
# document gets the same reading as a generated one.
#
# A product is named by its server URL. Every published document must match one.
PRODUCTS = {
    "https://business.gtowizard.com": {
        "name": "GTO Score",
        "prefixes": ("/v4/fair-play/gto-score/",),
        "schemes": {PUBLIC_SCHEME},
    },
    "https://api.gtowizard.com": {
        "name": "FairPlay",
        "prefixes": ("/v1/poker/fair-play/", "/v1/account/oauth/token/"),
        # The token call takes the client id and the client secret as HTTP Basic.
        # Every other call takes the access token.
        "schemes": {PUBLIC_SCHEME, BASIC_SCHEME},
    },
}

# The backend calls this document the business API, which is the name of the door,
# not the name of the product. The site holds more than one product, so it names
# each one.
TITLE = "GTO Score API"

DESCRIPTION = (
    "GTO Score reads the hand histories of a poker room and scores the decisions "
    "of a player against the solver.\n\n"
    "Send the access token of your application in the `Authorization` header: "
    "`Authorization: Bearer <access token>`. The guides explain how to get one."
)

BEARER = {
    "type": "http",
    "scheme": "bearer",
    "description": (
        "The OAuth2 access token of your application, from the client-credentials "
        "token call. See the Authentication guide."
    ),
}

# The wire formats a published document may declare. A document that declares a
# scheme of a different shape, for example an apiKey in a query parameter, would
# put the credential somewhere a partner must not put it, so the check refuses it.
ALLOWED_SCHEME_SHAPES = {
    PUBLIC_SCHEME: {"type": "http", "scheme": "bearer"},
    BASIC_SCHEME: {"type": "http", "scheme": "basic"},
}

# The error codes a GTO Score call can answer. The backend enum lists every code
# of the whole platform. The rest mean nothing to a partner.
PARTNER_ERROR_CODES = (
    "AUTHENTICATION_FAILED",
    "CONFLICT",
    "GTO_SCORE_EFFORT_NOT_SUPPORTED",
    "GTO_SCORE_MONTHLY_LIMIT_REACHED",
    "GTO_SCORE_NOT_ENABLED",
    "GTO_SCORE_TASK_IN_FLIGHT",
    "NOT_FOUND",
    "PERMISSION_DENIED",
    "UPLOAD_OBJECT_MISSING",
    "UPLOAD_TOO_LARGE",
    "VALIDATION_ERROR",
)

# Text that must never reach the public repository.
FORBIDDEN = {
    "repository path": re.compile(r"\b(?:docs|app|src|libs|tools|infra)/[\w./-]+"),
    "module path": re.compile(r"\bapp_\w+"),
    "source file": re.compile(r"\b[\w-]+\.(?:py|md|ya?ml|sh|tf|hcl)\b"),
    "ticket id": re.compile(r"\b(?:FPS|BE|OPS|INT|AI|TD|PLO|WEB|PA)-\d+\b"),
    "internal host": re.compile(r"\b[\w.-]*gtowiz\.(?:com|dev)\b"),
    "cloud resource": re.compile(r"\b(?:s3://|arn:aws|amazonaws\.com)"),
    "e-mail address": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
}
# Every gtowizard.com host except a public API host is internal.
GTOWIZARD_HOST = re.compile(r"\b(?:[\w-]+\.)+gtowizard\.com\b")
PUBLIC_HOSTS = {"business.gtowizard.com", "api.gtowizard.com"}


class SchemaError(Exception):
    pass


def operation_id(operation: dict) -> str:
    """The backend names an operation after its Python module path. Name it after its summary."""
    summary = operation.get("summary", "")
    slug = re.sub(r"[^a-z0-9]+", "_", summary.lower()).strip("_")
    if not slug:
        raise SchemaError(f"operation {operation.get('operationId')!r} has no summary")
    return slug


def prepare(doc: dict) -> dict:
    doc["info"]["title"] = TITLE
    doc["info"]["description"] = DESCRIPTION
    for operation in _operations(doc):
        operation["operationId"] = operation_id(operation)

    components = doc.setdefault("components", {})
    schemes = components.get("securitySchemes", {})
    unknown = sorted(set(schemes) - {SOURCE_SCHEME, PUBLIC_SCHEME})
    if unknown:
        raise SchemaError(f"unknown security schemes: {unknown}")
    components["securitySchemes"] = {PUBLIC_SCHEME: BEARER}
    for operation in _operations(doc):
        for requirement in operation.get("security", []):
            if SOURCE_SCHEME in requirement:
                requirement[PUBLIC_SCHEME] = requirement.pop(SOURCE_SCHEME)

    codes = components.get("schemas", {}).get("ErrorResponseCode")
    if codes is not None:
        missing = sorted(set(PARTNER_ERROR_CODES) - set(codes["enum"]))
        if missing:
            raise SchemaError(f"partner error codes absent from the source enum: {missing}")
        codes["enum"] = [code for code in codes["enum"] if code in PARTNER_ERROR_CODES]
    return doc


def check(doc: dict) -> list[str]:
    problems = []
    if not str(doc.get("openapi", "")).startswith("3."):
        problems.append("the document is not OpenAPI 3")

    # The server names the product, and the product says which paths and which
    # credentials are its own. An unknown server stops the check here: without a
    # product there is nothing to measure the rest of the document against.
    servers = [s.get("url") for s in doc.get("servers", [])]
    if len(servers) != 1 or servers[0] not in PRODUCTS:
        return sorted(
            set(
                problems
                + [f"servers must be exactly one of {sorted(PRODUCTS)}, got {servers}"]
            )
        )
    product = PRODUCTS[servers[0]]

    paths = list(doc.get("paths", {}))
    if not paths:
        problems.append("the document has no paths")
    problems += [
        f"{product['name']}: path outside {list(product['prefixes'])}: {p}"
        for p in paths
        if not p.startswith(product["prefixes"])
    ]

    schemes = doc.get("components", {}).get("securitySchemes", {})
    if set(schemes) != product["schemes"]:
        problems.append(
            f"{product['name']}: securitySchemes must be exactly {sorted(product['schemes'])}, "
            f"got {sorted(schemes)}"
        )
    for name, scheme in schemes.items():
        shape = ALLOWED_SCHEME_SHAPES.get(name)
        if shape is None:
            problems.append(f"security scheme {name!r} is not one this site publishes")
        elif {k: scheme.get(k) for k in shape} != shape:
            problems.append(f"security scheme {name!r} does not carry the credential as {shape}")

    ids = []
    for operation in _operations(doc):
        ids.append(operation.get("operationId"))
        if operation.get("summary") and operation.get("operationId") != operation_id(operation):
            problems.append(f"operationId {operation.get('operationId')!r} is not the slug of its summary")
        for requirement in operation.get("security", []):
            if set(requirement) - product["schemes"]:
                problems.append(f"operation {operation.get('operationId')} names {sorted(requirement)}")
    if len(ids) != len(set(ids)):
        problems.append("two operations share an operationId")
    codes = doc.get("components", {}).get("schemas", {}).get("ErrorResponseCode", {}).get("enum", [])
    problems += [f"error code not for partners: {c}" for c in codes if c not in PARTNER_ERROR_CODES]

    for text in _strings(doc):
        problems += check_text(text)
    return sorted(set(problems))


def _operations(doc: dict):
    for item in doc.get("paths", {}).values():
        for method, operation in item.items():
            if method in {"get", "put", "post", "delete", "patch", "head", "options", "trace"}:
                yield operation


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


def _write(doc: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_text(text: str) -> list[str]:
    problems = []
    for label, pattern in FORBIDDEN.items():
        problems += [f"{label}: {m.group(0)!r}" for m in pattern.finditer(text)]
    problems += [
        f"internal host: {m.group(0)!r}"
        for m in GTOWIZARD_HOST.finditer(text)
        if m.group(0) not in PUBLIC_HOSTS
    ]
    return sorted(set(problems))


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "--check-text":
        failed = False
        for name in argv[1:]:
            for problem in check_text(Path(name).read_text(encoding="utf-8")):
                print(f"{name}: {problem}", file=sys.stderr)
                failed = True
        return 1 if failed else 0
    if len(argv) >= 2 and argv[0] == "--check":
        failed = False
        for name in argv[1:]:
            problems = check(json.loads(Path(name).read_text(encoding="utf-8")))
            for problem in problems:
                print(f"{name}: {problem}", file=sys.stderr)
            failed |= bool(problems)
        return 1 if failed else 0
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    source, output = Path(argv[0]), Path(argv[1])
    try:
        doc = prepare(json.loads(source.read_text(encoding="utf-8")))
    except SchemaError as error:
        print(f"{source}: {error}", file=sys.stderr)
        return 1
    problems = check(doc)
    if problems:
        for problem in problems:
            print(f"{source}: {problem}", file=sys.stderr)
        print("Refusing to write a public schema. Fix the source first.", file=sys.stderr)
        return 1
    _write(doc, output)
    print(f"wrote {output}: {len(doc['paths'])} paths")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
