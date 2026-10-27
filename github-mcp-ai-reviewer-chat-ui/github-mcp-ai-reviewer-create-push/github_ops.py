"""Small, explicit GitHub REST operations for the human-approved PR workflow."""
import base64
import re
import requests

API = "https://api.github.com"
HEADERS_BASE = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _headers(token):
    if not token or token.startswith("replace_with_"):
        raise RuntimeError("Configure a real GITHUB_TOKEN in .env.")
    return {**HEADERS_BASE, "Authorization": f"Bearer {token}"}


def _request(method, path, token, **kwargs):
    response = requests.request(method, f"{API}{path}", headers=_headers(token), timeout=40, **kwargs)
    if response.status_code >= 400:
        try:
            message = response.json().get("message", response.text[:300])
        except ValueError:
            message = response.text[:300]
        raise RuntimeError(f"GitHub API {response.status_code}: {message}")
    return response.json() if response.content else {}


def get_repo(token, repo):
    return _request("GET", f"/repos/{repo}", token)


def list_text_files(token, repo, branch):
    data = _request("GET", f"/repos/{repo}/git/trees/{branch}", token, params={"recursive": "1"})
    files = []
    for item in data.get("tree", []):
        path = item.get("path", "")
        if item.get("type") == "blob" and not any(part.startswith(".") for part in path.split("/")) and not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".dll", ".bin", ".parquet", ".xlsx", ".xls")):
            files.append(path)
    return files


def get_file(token, repo, path, branch):
    from urllib.parse import quote
    data = _request("GET", f"/repos/{repo}/contents/{quote(path, safe='/')}", token, params={"ref": branch})
    if data.get("encoding") != "base64":
        raise RuntimeError("GitHub did not return a base64 text file.")
    try:
        content = base64.b64decode(data["content"]).decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("Selected file is not UTF-8 text. Choose a source/configuration file.") from exc
    return content, data["sha"]


def create_pull_request_with_file(token, repo, base_branch, filename, old_sha, new_content, title, body, commit_message):
    """Create a new branch, commit one approved file replacement, and open a PR.

    Called only after explicit UI confirmation. Never merges the PR.
    """
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise RuntimeError("Repository must be owner/repository.")
    if not filename or filename.startswith("/") or ".." in filename.split("/"):
        raise RuntimeError("Unsafe file path rejected.")
    safe_branch = "ai-review/" + re.sub(r"[^A-Za-z0-9._/-]+", "-", filename.replace("/", "-"))[:45].strip("-.") + "-proposal"
    # Ensure unique branch name if a previous attempt used it.
    import time
    branch = f"{safe_branch}-{int(time.time())}"
    ref = _request("GET", f"/repos/{repo}/git/ref/heads/{base_branch}", token)
    base_sha = ref["object"]["sha"]
    _request("POST", f"/repos/{repo}/git/refs", token, json={"ref": f"refs/heads/{branch}", "sha": base_sha})
    from urllib.parse import quote
    payload = {"message": commit_message[:200], "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"), "branch": branch, "sha": old_sha}
    _request("PUT", f"/repos/{repo}/contents/{quote(filename, safe='/')}", token, json=payload)
    pr = _request("POST", f"/repos/{repo}/pulls", token, json={"title": title[:250], "head": branch, "base": base_branch, "body": body + f"\n\nAI-proposed change to `{filename}`. Human review required; this PR was not merged."})
    return {"branch": branch, "pr_number": pr["number"], "html_url": pr["html_url"], "title": pr["title"]}



def suggest_repository_names(description, llm_function):
    """Use the configured LLM to suggest concise repository names and descriptions."""
    prompt = (
        "Suggest 8 GitHub repository names for this software project. "
        "Names must be lowercase kebab-case, 2-5 words, memorable, professional, "
        "and suitable for a public engineering portfolio. Avoid spaces and underscores. "
        "Return ONLY a JSON array of objects with keys name and description.\n\n"
        f"Project description: {description[:3000]}"
    )
    return llm_function(prompt)


def create_repository(token, name, description, private=True):
    """Create a GitHub repository for the authenticated user."""
    if not re.fullmatch(r"[a-zA-Z0-9._-]{1,100}", name):
        raise RuntimeError("Repository name must use letters, numbers, dots, hyphens, or underscores.")
    return _request("POST", "/user/repos", token, json={
        "name": name, "description": description[:350], "private": bool(private),
        "auto_init": True, "has_issues": True, "has_projects": False, "has_wiki": False
    })


def push_local_project_as_commit(token, full_name, local_root, commit_message="Initial project upload"):
    """Upload safe text/source files from the running project as one Git commit via GitHub API.

    Excludes secrets, virtual environments, VCS metadata, caches, and generated binaries.
    This pushes the current app project, not an arbitrary path from a browser.
    """
    import os, base64
    from pathlib import Path
    root = Path(local_root).resolve()
    excluded_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache", ".ruff_cache"}
    excluded_files = {".env", "credentials.json", "secrets.json"}
    binary_exts = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".dll", ".bin", ".parquet", ".xlsx", ".xls", ".pyc", ".db", ".sqlite"}
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in excluded_dirs for part in rel.parts):
            continue
        if path.name in excluded_files or path.name == ".env" or path.suffix.lower() in binary_exts:
            continue
        if path.name.endswith((".secret", ".pem", ".key")):
            continue
        if path.stat().st_size > 500_000:
            continue
        try:
            content = path.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        files.append((rel.as_posix(), content))
    if not files:
        raise RuntimeError("No eligible text/source files found to push.")
    if len(files) > 150:
        raise RuntimeError(f"Found {len(files)} files; safety limit is 150 files per initial push.")

    repo_data = _request("GET", f"/repos/{full_name}", token)
    # auto_init creates the default branch and initial commit.
    default_branch = repo_data.get("default_branch") or "main"
    ref = _request("GET", f"/repos/{full_name}/git/ref/heads/{default_branch}", token)
    base_commit_sha = ref["object"]["sha"]
    base_commit = _request("GET", f"/repos/{full_name}/git/commits/{base_commit_sha}", token)
    base_tree_sha = base_commit["tree"]["sha"]
    tree_items = []
    for rel, content in files:
        blob = _request("POST", f"/repos/{full_name}/git/blobs", token, json={"content": content, "encoding": "utf-8"})
        tree_items.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = _request("POST", f"/repos/{full_name}/git/trees", token, json={"base_tree": base_tree_sha, "tree": tree_items})
    commit = _request("POST", f"/repos/{full_name}/git/commits", token, json={
        "message": commit_message[:200], "tree": tree["sha"], "parents": [base_commit_sha]
    })
    _request("PATCH", f"/repos/{full_name}/git/refs/heads/{default_branch}", token, json={"sha": commit["sha"], "force": False})
    return {"url": repo_data["html_url"], "branch": default_branch, "files_count": len(files), "commit_sha": commit["sha"]}
