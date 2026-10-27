# GitHub AI Code Reviewer — FDE Portfolio Project

Streamlit application that reviews existing GitHub pull requests and proposes a focused one-file code change using OpenAI `gpt-4o-mini` (or optional Gemini). The app previews a unified diff and requires a checkbox plus typed confirmation before creating a branch, committing the selected file replacement, and opening a pull request. It never merges a PR or executes repository code.

## Architecture

- `app.py`: Streamlit UI, PR review, proposal preview, explicit approval gate.
- `llm.py`: LLM calls, review prompt, proposed-file JSON validation and source-size guardrail.
- `github_ops.py`: narrow GitHub REST operations for repository/tree/file reads and branch/commit/PR creation.
- `mcp_client.py`: official GitHub MCP server initialization handshake and read-only tool discovery (diagnostic; PR workflows currently use REST API).

## Windows setup

1. Install Python 3.12 and Docker Desktop (Docker is only needed for the MCP handshake diagnostic).
2. Extract the ZIP and open PowerShell in the project directory.
3. Run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

4. In `.env`, set `LLM_PROVIDER=openai`, `OPENAI_API_KEY` and `GITHUB_TOKEN`; default model is `gpt-4o-mini`.
5. Run `streamlit run app.py`.

## GitHub token permissions

Use a fine-grained PAT limited to the target repository. Read/review needs repository metadata, contents read, and pull requests read. AI-assisted PR creation additionally needs **Contents: Read and write** and **Pull requests: Read and write**. Grant only what you need. Never commit `.env` or paste tokens into issues/prompts.

## Workflow

### Review an existing PR

1. Enter `owner/repository` and click **Load open pull requests**.
2. Select a PR and choose **Analyze PR with AI**.
3. Inspect the report; optionally approve and post the review comment by checking the box and typing `POST COMMENT`.

### AI-assisted PR creation

1. Open **AI-assisted PR creation**.
2. Click **Load source files**, choose a small text/source file, and describe one focused change.
3. Generate the proposed fix. Inspect the PR title, description and complete unified diff.
4. Run tests locally where applicable. If the diff is acceptable, check the approval box and type `CREATE PULL REQUEST`.
5. The app creates a branch, commits the complete replacement of that one file, and opens a PR against the repository's default branch. It never merges it.

## MCP handshake

Click **Initialize MCP & handshake** in the sidebar. This starts the official GitHub MCP server through Docker, calls the SDK's `session.initialize()`, then lists tools. This is a read-only diagnostic session and closes after discovery. The current application workflow uses GitHub REST API calls for its repository and PR operations; it does not yet route those operations through MCP tool calls.

## Tests

```powershell
pytest -q
```

Tests mock LLM calls and validate provider configuration and diff size guardrails. Live API calls require your own credentials and are not part of unit tests.

## Deployment

For a private deployment, use a host that supports Python/Streamlit and inject secrets through the platform's secret manager. Do not commit `.env`. The MCP handshake button requires Docker availability on the host; the rest of the REST-based app does not require Docker. Before public deployment, add user authentication, per-user authorization, audit logs, rate limiting, CSRF/session review, and isolated evaluation/test execution.

## Limitations

- Proposes changes to one existing text file per PR; it does not create new files or execute tests automatically.
- Large files are rejected by a configurable size limit.
- AI output can be wrong. Review the diff and run tests before merging.
- GitHub API write permissions are needed only for the explicit branch/commit/PR creation action.

## Repository understanding workflow

In the **AI-assisted PR creation** tab, enter `owner/repository`, click **Read & understand this GitHub project**, and review the AI orientation report and candidate file tree. The initial scan reads the default branch's file paths and README; it does not claim to have read every source file. Next, enter a plain-English change request, choose a source file, and click **Read selected file & generate AI fix**. The app fetches that file's current content and SHA, combines it with the repository map and your request, and asks the configured LLM for a proposed replacement. Inspect the diff and PR description. Only after checking the approval box and typing `CREATE PULL REQUEST` does the app create a branch, commit the selected file replacement, and open a PR. It does not merge PRs or execute repository code.

The current PR-creation implementation intentionally supports one existing text file per proposal. For changes spanning multiple files, make separate reviewed proposals or extend the workflow to generate and validate a multi-file patch before enabling writes.


## Create a repository and push this project

The Streamlit app includes **Create a GitHub repository & push this project**. Enter a project description and select **Generate repository name ideas with AI** to get names from the configured LLM. Choose public/private visibility, review the name, then tick the approval checkbox and type `CREATE AND PUSH`. The app creates the repository for the authenticated GitHub user and uploads eligible source/text files as one initial commit using GitHub's Git Data API.

Safety exclusions include `.env`, VCS metadata, virtual environments, caches, common binary files, secret/key files, files larger than 500 KB, and projects with more than 150 eligible files. The operation uploads the current app's project folder. It does not upload an arbitrary path supplied by a browser. Use a fine-grained token with **Administration: Read and write** to create repositories and **Contents: Read and write** to upload files. Keep the token private.
