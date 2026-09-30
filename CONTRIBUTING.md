# Contributing to YTD

Thanks for your interest in improving YTD.

## Reporting a Bug

Before reporting a bug, please update YTD with `update.ps1` and reproduce the problem.

Include:

- Windows version
- Python version
- YTD version
- Whether it was an individual video or playlist
- Selected quality
- Sequential or parallel mode
- The relevant error output
- Relevant parts of `download_report.txt`

Do not include cookies, authentication tokens, private URLs, or other sensitive information.

## Suggestions

Feature suggestions are welcome. Explain the user problem first, then describe the proposed solution.

## Pull Requests

1. Keep changes focused.
2. Do not commit third-party binaries.
3. Keep the CLI understandable for non-technical users.
4. Test both individual-video and playlist flows when changing download logic.
5. Run the syntax test before opening a pull request.

```powershell
python tests/test_syntax.py
```
