from llm import review_pull_request


def test_provider_validation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")
    try:
        review_pull_request("owner/repo", {"number": 1, "title": "test"}, [])
    except RuntimeError as exc:
        assert "LLM_PROVIDER" in str(exc)
    else:
        raise AssertionError("Unsupported provider should fail clearly")


def test_diff_size_guardrail(monkeypatch):
    monkeypatch.setenv("MAX_DIFF_CHARS", "10")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    import llm
    captured = {}
    def fake_gemini(prompt, system):
        captured["prompt"] = prompt
        return "Mock review"
    monkeypatch.setattr(llm, "_gemini", fake_gemini)
    result = review_pull_request("owner/repo", {"number": 1, "title": "t"}, [{"filename": "a.py", "patch": "+" + "x" * 100}])
    assert result == "Mock review"
    assert "MAX_DIFF_CHARS" in captured["prompt"]
