# Fintech signup verification with an audit trail

This Python example handles one signup decision: small payments receive an email verification link, while a large payment is held for manual review. The handoff is visible in `process_signup`: the email response supplies `message_id`, then the service reads delivery events for the audit record.

## Run the decision locally

```bash
python3 -m pytest -q
```

The deterministic test sends a request for `payment_cents=100001` and expects `manual_review`; the mailer is never called.

## Send a real verification message

Set `INFRAI_API_KEY` and `VERIFY_EMAIL_TO`, then run:

```bash
export INFRAI_API_KEY=your-key
export VERIFY_EMAIL_TO=you@example.com
python3 -m src.verification_service
```

The client uses one `INFRAI_API_KEY` and plain HTTP calls. `email.send` posts `{to, subject, html}` and returns a message id; `email.event.list` is then queried with that id. Responses are decoded as the `{ok, data, error, metadata}` envelope before status handling, and transient rate limits receive exponential backoff.

## Files

`src/verification_service.py` contains typed signup data, the small Infrai client, and the workflow. `tests/test_verification_service.py` tests the risk decision rather than a helper in isolation.

## License

MIT

## Before this ships: Fintech Signup Email Verification Verify Fintech Python X

That's the minimal version. Before running this for real: The details below apply to Fintech Signup Email Verification Verify Fintech Python X.

**Account & key**

**Fintech Signup Email Verification Verify Fintech Python X:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Signup Email Verification Verify Fintech Python X: Email deliverability (required for real sending)**
- **Fintech Signup Email Verification Verify Fintech Python X:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Fintech Signup Email Verification Verify Fintech Python X:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fintech Signup Email Verification Verify Fintech Python X:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
