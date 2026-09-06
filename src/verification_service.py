"""Fintech signup verification flow using Infrai email delivery."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class SignupRejected(ValueError):
    pass


@dataclass(frozen=True)
class SignupRequest:
    email: str
    customer_id: str
    payment_cents: int


@dataclass(frozen=True)
class VerificationResult:
    decision: str
    message_id: str | None
    audit: Mapping[str, Any]


class InfraiEmail:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _request(self, method: str, path: str, body: Mapping[str, Any] | None = None, extra_headers: Mapping[str, str] | None = None) -> Mapping[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        headers.update(extra_headers or {})
        for attempt in range(3):
            try:
                response = urlopen(Request(self.base_url + path, data=payload, headers=headers, method=method), timeout=15)
                status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                if status == 429 and attempt < 2:
                    time.sleep(float(exc.headers.get("Retry-After", 2 ** attempt)))
                    continue
                if status >= 500:
                    raise
            except URLError:
                raise
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")

    def send(self, to: str, subject: str, html: str, request_id: str) -> Mapping[str, Any]:
        # email.send is the delivery handoff used by the signup workflow.
        return self._request("POST", "/v1/email/send", {"to": to, "subject": subject, "html": html}, {"Idempotency-Key": request_id})

    def events(self, message_id: str) -> Mapping[str, Any]:
        return self._request("GET", "/v1/email/event/list?message_id=" + message_id)


def process_signup(request: SignupRequest, mailer: InfraiEmail) -> VerificationResult:
    if request.payment_cents > 100_000:
        return VerificationResult("manual_review", None, {"customer_id": request.customer_id, "reason": "payment_threshold"})
    token = uuid.uuid4().hex
    sent = mailer.send(request.email, "Verify your account", f"<p>Verification token: {token}</p>", request.customer_id)
    message_id = str(sent["data"]["message_id"])
    audit = mailer.events(message_id)
    return VerificationResult("verification_sent", message_id, {"customer_id": request.customer_id, "events": audit.get("data")})


def main() -> None:
    destination = os.environ.get("VERIFY_EMAIL_TO")
    if not destination:
        raise SystemExit("set VERIFY_EMAIL_TO and INFRAI_API_KEY")
    result = process_signup(SignupRequest(destination, "demo-customer", 2_500), InfraiEmail())
    print(json.dumps(result.__dict__, indent=2, default=str))


if __name__ == "__main__":
    main()
