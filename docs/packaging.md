# Desktop packaging

The Tk launcher starts a dashboard at `http://127.0.0.1:18766` and opens it in the default browser. Keep the launcher window open to use the dashboard. The launcher keeps its SQLite data in a per-user application data directory. A source checkout or another instance can have a separate database.

| Platform | Package | How to run |
| --- | --- | --- |
| macOS Apple Silicon | `Career-Agent-macOS-arm64.dmg` | Mount the image, drag Career Agent into Applications, then open the app. |
| Windows x64 | `Career-Agent-Windows-x64.exe` | Run the portable executable directly. |
| Linux x64 (DEB, glibc 2.35 or later) | `career-agent-linux-amd64.deb` | On a desktop with APT, run `sudo apt install ./career-agent-linux-amd64.deb` and open Career Agent from the application menu. |

Preview builds lack Developer ID signing, macOS notarization, and Windows Authenticode signing. Your operating system may warn about opening them. Linux support is smoke tested on the Ubuntu 22.04 runner.

GitHub Actions builds and tests each artifact on its target operating system before uploading it. The macOS job verifies and mounts the DMG, then copies the app out of the image for the test. The Windows job launches the portable EXE. The Linux job installs the DEB and runs the launcher through a virtual display. The same smoke test checks that the launcher serves the dashboard and its JavaScript and CSS, starts with an empty test database, and preserves a test profile after restart. It uses a temporary database and makes no requests to job boards or AI providers. CI outputs are available as workflow artifacts.

MCP requires a Python environment with the optional `requirements-mcp.txt` dependencies and is launched separately from the packaged dashboard. Codex and Claude review require a compatible, authenticated CLI on the application’s `PATH`. Packaged smoke tests cover the desktop and local data workflow. Live provider access depends on the user's configuration.

When connecting MCP to the desktop launcher, set `CAREER_PORT=18766` and point `CAREER_DB_PATH` at the launcher's database in the MCP client's environment. The default database paths are:

- macOS: `~/Library/Application Support/Career Agent/jobs.sqlite3`
- Windows: `%LOCALAPPDATA%\Career Agent\jobs.sqlite3`
- Linux: `$XDG_DATA_HOME/career-agent/jobs.sqlite3` or `~/.local/share/career-agent/jobs.sqlite3`
