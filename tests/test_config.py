from pathlib import Path

from whatsthenew.config import Settings

_RELEVANT = [
    "PLAN_DIR",
    "PLAN_FILE",
    "PROPOSED_PLAN_FILE",
    "PUBLISH_PROPOSAL",
    "PLAN_REPO",
    "PLAN_REPO_TOKEN",
    "PROPOSAL_BRANCH_PREFIX",
]


def _clear(monkeypatch):
    for key in _RELEVANT:
        monkeypatch.delenv(key, raising=False)


def test_plan_file_derives_from_plan_dir(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("PLAN_DIR", "/tmp/whatsthenew-plan")
    settings = Settings.from_env()
    assert settings.plan_dir == Path("/tmp/whatsthenew-plan")
    assert settings.plan_file == Path("/tmp/whatsthenew-plan/GOD_PLAN.md")


def test_plan_file_explicit_override(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("PLAN_DIR", "/tmp/x")
    monkeypatch.setenv("PLAN_FILE", "/tmp/x/otro.md")
    assert Settings.from_env().plan_file == Path("/tmp/x/otro.md")


def test_publish_proposal_flag(monkeypatch):
    _clear(monkeypatch)
    assert Settings.from_env().publish_proposal is False
    monkeypatch.setenv("PUBLISH_PROPOSAL", "1")
    assert Settings.from_env().publish_proposal is True
    monkeypatch.setenv("PUBLISH_PROPOSAL", "no")
    assert Settings.from_env().publish_proposal is False


def test_proposal_branch_prefix_default(monkeypatch):
    _clear(monkeypatch)
    assert Settings.from_env().proposal_branch_prefix == "proposal"
    monkeypatch.setenv("PROPOSAL_BRANCH_PREFIX", "propuesta")
    assert Settings.from_env().proposal_branch_prefix == "propuesta"


def test_plan_repo_token_defaults_empty(monkeypatch):
    _clear(monkeypatch)
    settings = Settings.from_env()
    assert settings.plan_repo == ""
    assert settings.plan_repo_token == ""
