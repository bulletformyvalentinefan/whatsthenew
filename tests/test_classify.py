from whatsthenew.classify import (
    classify,
    detect_level,
    detect_remote,
    extract_skills,
    extract_years,
)

STACK = ["kubernetes", "terraform", "aws", "docker", "python", "go"]


def test_detect_level_senior():
    assert detect_level("Senior DevOps Engineer") == "senior"


def test_detect_level_junior():
    assert detect_level("Junior Cloud Engineer") == "junior"


def test_detect_level_semi():
    assert detect_level("Semi Senior Backend") == "semi"


def test_detect_level_none():
    assert detect_level("Platform Engineer") == ""


def test_extract_years():
    assert extract_years("5+ years of experience with Kubernetes") == [5]
    assert extract_years("3 años y 6 años") == [3, 6] or extract_years("3 años y 6 años") == [3, 6]


def test_extract_skills():
    got = extract_skills("We use Kubernetes, Terraform and AWS", STACK)
    assert "kubernetes" in got and "terraform" in got and "aws" in got


def test_detect_remote_true():
    assert detect_remote("Remote - worldwide") is True


def test_detect_remote_hybrid_is_false():
    assert detect_remote("Melbourne", "hybrid role") is False


def test_classify_bundle():
    out = classify("Senior SRE", "5 years with Go and Kubernetes, remote", STACK, "Remote")
    assert out["level"] == "senior"
    assert 5 in out["years"]
    assert "kubernetes" in out["skills"]
    assert out["remote"] is True
