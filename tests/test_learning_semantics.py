from services.learning.semantics import infer_reminder_feedback_semantics


def test_dismiss_with_quick_followup_is_positive_signal():
    result = infer_reminder_feedback_semantics(
        action="dismissed", followup_action_within_minutes=20
    )
    assert result.usefulness >= 0.8
    assert result.timing_fit >= 0.6


def test_dismiss_without_followup_is_low_usefulness():
    result = infer_reminder_feedback_semantics(action="dismissed")
    assert result.usefulness <= 0.3


def test_snooze_is_useful_but_mistimed_signal():
    result = infer_reminder_feedback_semantics(action="snoozed", snooze_minutes=10)
    assert result.usefulness >= 0.7
    assert result.timing_fit <= 0.4
    assert result.interrupt_cost >= 0.7
