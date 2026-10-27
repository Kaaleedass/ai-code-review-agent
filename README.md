# AI Code Review Agent

An AI-powered GitHub code review agent built with Python, Streamlit, OpenAI GPT-4o mini, and the GitHub MCP Server. It helps developers understand existing repositories, analyze source code, propose targeted fixes, and create pull requests with explicit human approval.

## Key Features

- **GitHub Repository Discovery** — Load and select repositories accessible to your GitHub token.
- **Repository Understanding** — Retrieve repository metadata, README content, file trees, and relevant source files.
- **AI-Powered Code Review** — Analyze code and generate targeted improvement suggestions using GPT-4o mini.
- **Diff Preview** — Inspect proposed changes before publishing them.
- **Human-in-the-Loop Approval** — Require explicit confirmation before creating a branch, committing changes, and opening a pull request.
- **Pull Request Workflow** — Review existing pull requests and create AI-assisted pull requests.
- **GitHub MCP Integration** — Connect to the official GitHub MCP Server and discover available tools.
- **Repository Creation** — Support creating a new GitHub repository and pushing the project source files.

## Architecture

```text
User
 |
 v
Streamlit Web Interface
 |
 v
Python Application
 |
 +--------------------+
 |                    |
 v                    v
GitHub REST API    GitHub MCP Server
 |                    |
 +----------+---------+
            |
            v
   Repository Context
            |
            v
   OpenAI GPT-4o mini
            |
            v
   Proposed Code Changes
            |
            v
      Diff Preview
            |
            v
   Human Approval Gate
            |
            v
   Branch + Commit + PR
```

The GitHub REST API handles repository operations in the application. The MCP integration provides a standardized interface for discovering GitHub tools. The application uses explicit approval before publishing proposed changes.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and orchestration |
| Streamlit | Interactive web interface |
| OpenAI GPT-4o mini | Code analysis and fix generation |
| GitHub REST API | Repository access and pull-request operations |
| GitHub MCP Server | MCP protocol and GitHub tool discovery |
| Docker | Runs the MCP server locally |
| GitHub | Source control and pull-request workflow |

## Prerequisites

- Python 3.12 or a compatible Python version
- GitHub account and a personal access token
- OpenAI API key
- Docker Desktop with the Linux container backend enabled
- Access to the target GitHub repository

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-code-review-agent.git
cd ai-code-review-agent
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and configure the required values according to the project's settings.

Example:

```dotenv
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_personal_access_token
```

Use the exact GitHub token variable expected by your application's code. Never commit `.env` or expose API keys, tokens, or other credentials.

### 5. Start Docker Desktop

Ensure Docker Desktop is running before initializing the GitHub MCP Server.

If the server image has not already been downloaded:

```powershell
docker pull ghcr.io/github/github-mcp-server:latest
```

### 6. Run the application

```powershell
streamlit run app.py
```

Open the local URL displayed in your terminal, usually `http://localhost:8501`.

## How to Use

1. Open the application and initialize the GitHub MCP connection.
2. Load your accessible GitHub repositories.
3. Select the
