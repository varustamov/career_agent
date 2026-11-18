# Private VPS deployment preparation

This service template has not yet been installed or verified on the target VPS.
It serves the dashboard on 127.0.0.1:18765 only and stores its database separately
in /var/lib/career-agent. Provision the dedicated account, directories and files
only after checking existing services and confirming target paths and Python.
Connect using an authenticated SSH tunnel, e.g. `ssh -L 18765:127.0.0.1:18765 user@server`,
then visit http://127.0.0.1:18765 on the client. Do not expose the dashboard to the
Internet: the existing application has no multi-user authentication or isolation.

Deploying code alone creates a fresh database; user data migration requires a
consistent SQLite backup, access controls and validation. Existing AI schedules,
if migrated, may start when the server starts. The systemd user also needs its
own authorized Codex/Claude installation and credentials for AI features; local
Mac sessions and browser logins are not automatically available on the VPS.

The service file does not implement OAuth, HTTPS, a public landing page, installer
downloads, or a callback. The portfolio domain currently points to another service;
changing it would require verifying the hosting configuration and avoiding disruption.
