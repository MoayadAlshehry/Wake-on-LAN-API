# Linux service setup

First confirm that `wakeonlan <your target MAC>` works from the Linux host and that your Tailscale route is usable. The application cannot fix firmware or network broadcast restrictions.

1. Place the repository in `/opt/wol` and create `/opt/wol/.venv`.
2. Install `requirements.txt` into that environment.
3. Create a dedicated unprivileged `wolapi` service account, with read/execute access to the application and environment.
4. Store the reviewed configuration in `/etc/wol-api.env`. Use a random API token, a specific Tailscale bind address, and port 5000. Restrict the file to root and the service group (for example `root:wolapi`, mode 0640).
5. Review and copy [`examples/wol-api.service`](../examples/wol-api.service) into `/etc/systemd/system/wol-api.service`.
6. Run `sudo systemctl daemon-reload`, then `sudo systemctl enable --now wol-api`.
7. Inspect `sudo systemctl status wol-api` and `sudo journalctl -u wol-api` if it fails.

The example runs Gunicorn as an unprivileged user. Root is unnecessary for sending the packet. Keep access restricted through your Tailscale policy and server networking; the bearer token is an additional application control.

Test `GET /health`, an unauthenticated request (expected 401), and an authenticated POST from the intended client. A `sent` response confirms command completion only. Verify the target PC independently.
