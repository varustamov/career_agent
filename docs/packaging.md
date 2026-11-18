# Desktop packaging

The Tk launcher starts a loopback-only dashboard and keeps it running until the user quits the launcher. It uses an OS-specific per-user application-data directory; it does not migrate a source checkout's database automatically.

A local macOS Apple Silicon preview is built with PyInstaller and packaged as a DMG. The application is not signed or notarized. The workflow builds Windows `.exe`, Linux `.deb`, and macOS `.dmg` artifacts on their respective operating systems. Artifacts are not automatically published as releases. Platform builds require a successful CI run and testing on those platforms before they are advertised as available downloads.

Optional MCP integration requires a Python environment with the MCP SDK; the packaged app does not currently bundle a separately launchable MCP server. Codex and Claude integrations require a compatible installed and authenticated CLI, and have not been end-to-end validated in packaged distributions.
