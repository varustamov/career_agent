# Career Agent

An early open-source job search workspace. Search supported public feeds and company career pages, organize saved jobs, and optionally review them with a locally installed Codex or Claude CLI.

[Product page and preview downloads](https://vladimirarustamov.online/careeragent/)

**Status: early preview.** Applications are completed on the employer's website. Account connections, Agent Browser workflows and automatic applications are not yet implemented. HeadHunter search is disabled after HTTP 403 in the tested environment. Job matches are preliminary; verify eligibility, location and salary.

## Run from source

Python 3.10+ is required. No extra dependencies are needed for the dashboard.

```sh
python3 dashboard_server.py
```

Open http://127.0.0.1:8765. To use the small desktop launcher instead, run `python3 desktop.py` (Tk must be available). The launcher keeps the server running while its window is open and saves data in your user application-data directory.

## Search and privacy

Add search keywords in **Profile and sources**, then select public feeds or enter company career-page URLs for Greenhouse, Lever, Ashby or SmartRecruiters. Save your settings and run a search. The search is local to the running machine, but source APIs receive search requests. AI review sends the selected profile and job data to your chosen AI provider. Source content is untrusted; review all model output.

Enable profile and job sharing for your chosen provider in the dashboard before using AI review. Schedules created before this permission was introduced require a fresh opt-in.

The dashboard binds to loopback and has no multi-user authentication. Do not expose it publicly. A private server can be reached through an SSH tunnel; local and server databases do not automatically synchronize. The scheduling feature only runs while the application is running.

## MCP integration

An experimental MCP bridge lets trusted Codex or Claude clients read local jobs and profile data, start searches and manage AI review schedules. Install the optional SDK with `python3 -m pip install -r requirements-mcp.txt`, then register `career_mcp.py` with your client. The dashboard must be running for search and schedule operations. Connecting a client grants it access to your personal data. See [the detailed guide](docs/README.ru.md).

## Build

The desktop launcher can be packaged with PyInstaller. Windows, macOS and Linux builds must run on their respective platforms; `.github/workflows/build.yml` builds platform artifacts. Release signing and notarization are not configured. See the workflow and the [desktop packaging notes](docs/packaging.md).

## Development

```sh
python3 -m pip install -r requirements-mcp.txt
python3 -m unittest discover -s tests
```

The SQLite database, résumés, credentials and local build outputs must never be committed. Review `.gitignore` before publishing changes.

For a new job source, start with `source_registry.py`, `source_setup.py` and `sources.py`. The dashboard API and search coordination are in `dashboard_server.py`. The MCP bridge lives in `career_mcp.py`.

## License

MIT. See [LICENSE](LICENSE).
