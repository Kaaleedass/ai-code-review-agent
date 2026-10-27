import json
import pytest
import llm


def test_propose_file_fix_validates_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("MAX_SOURCE_CHARS", "1000")
    monkeypatch.setattr(llm, "_openai_compatible", lambda prompt, system: json.dumps({
        "pr_title": "Validate quantity", "pr_body": "Adds validation.",
        "commit_message": "Add quantity validation", "updated_content": "def f():\n    return 1\n"
    }))
    result = llm.propose_file_fix("owner/repo", "a.py", "def f():\n    return 0\n", "Change return value")
    assert result["pr_title"] == "Validate quantity"
    assert "return 1" in result["updated_content"]


def test_propose_file_fix_rejects_oversize(monkeypatch):
    monkeypatch.setenv("MAX_SOURCE_CHARS", "3")
    with pytest.raises(RuntimeError, match="limit"):
        llm.propose_file_fix("owner/repo", "a.py", "long content", "fix")


def test_propose_file_fix_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm, "_openai_compatible", lambda prompt, system: "not json")
    with pytest.raises(RuntimeError, match="valid JSON"):
        llm.propose_file_fix("owner/repo", "a.py", "x=1", "fix")
