from core.apply_queue import is_valid_transition


def test_valid_transitions():
    assert is_valid_transition("queued", "loading")
    assert is_valid_transition("loading", "filling")
    assert is_valid_transition("filling", "paused_review")
    assert is_valid_transition("paused_review", "submitted")
    assert is_valid_transition("paused_review", "blocked_login")
    assert is_valid_transition("paused_review", "blocked_captcha")


def test_invalid_transitions():
    assert not is_valid_transition("queued", "submitted")
    assert not is_valid_transition("submitted", "queued")
    assert not is_valid_transition("blocked_login", "submitted")
