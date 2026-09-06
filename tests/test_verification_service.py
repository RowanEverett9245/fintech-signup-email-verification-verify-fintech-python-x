from src.verification_service import SignupRequest, VerificationResult, process_signup


class NoSendMailer:
    def send(self, *args, **kwargs):
        raise AssertionError("manual review must not send")


def test_large_payment_is_held_for_manual_review():
    result = process_signup(SignupRequest("user@example.com", "cus-9", 100_001), NoSendMailer())
    assert result == VerificationResult("manual_review", None, {"customer_id": "cus-9", "reason": "payment_threshold"})
