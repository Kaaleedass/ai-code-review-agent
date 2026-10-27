# Security notes

- Keep GitHub and LLM credentials in `.env` or a deployment secret manager; never commit them.
- Use a fine-grained GitHub token limited to the intended repository. PR creation requires contents and pull request write permissions.
- Read and inspect the generated diff. Write actions require both a checkbox and typed confirmation.
- The app only replaces one existing file, creates a separate branch, and opens a PR; it does not merge or execute repository code.
- Repository content can contain prompt-injection attempts. It is passed as untrusted data; do not treat model output as authoritative.
- Run tests and review generated changes before merging. Do not deploy this starter publicly without authentication and stronger access controls.
