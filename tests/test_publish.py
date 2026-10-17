from datetime import UTC, datetime

from whatsthenew.publish import (
    is_plausible_plan,
    iso_week_branch,
    proposal_file_name,
    redact,
    render_pr_body,
)


def test_iso_week_branch_format():
    # 2026-01-05 es lunes de la semana ISO 2.
    assert iso_week_branch("proposal", datetime(2026, 1, 5, tzinfo=UTC)) == "proposal/2026-W02"


def test_iso_week_branch_two_digits():
    assert "-W0" in iso_week_branch("proposal", datetime(2026, 1, 5, tzinfo=UTC))


def test_proposal_file_name():
    assert proposal_file_name("proposal/2026-W02") == "proposal-2026-W02.md"


def test_is_plausible_plan_rejects_empty_and_short():
    assert is_plausible_plan("") is False
    assert is_plausible_plan("   ") is False
    assert is_plausible_plan("muy corto") is False


def test_is_plausible_plan_accepts_real_plan():
    assert is_plausible_plan("# Plan de carrera\n" + "contenido " * 40) is True


def test_redact_hides_token():
    assert redact("auth abc123 fail", "abc123") == "auth *** fail"
    assert redact("sin token", "") == "sin token"


def test_render_pr_body_includes_context():
    body = render_pr_body("proposal/2026-W02", 42, "17/10/2026 18:00", "proposals/proposal-2026-W02.md")
    assert "proposal/2026-W02" in body
    assert "42" in body
    assert "proposals/proposal-2026-W02.md" in body
