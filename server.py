"""A small authenticated API for a single, configured Wake-on-LAN target."""
from dataclasses import dataclass
import hmac
import ipaddress
import os
import re
import subprocess

from dotenv import load_dotenv
from flask import Flask, jsonify, request


@dataclass(frozen=True)
class Settings:
    target_mac: str
    token: str
    broadcast: str = "255.255.255.255"
    host: str = "127.0.0.1"
    port: int = 5000

    def __post_init__(self):
        if not re.fullmatch(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", self.target_mac):
            raise ValueError("WOL_TARGET_MAC must contain six colon-separated hexadecimal pairs.")
        if len(self.token) < 24:
            raise ValueError("WOL_API_TOKEN must contain at least 24 characters. Generate a random token.")
        if not isinstance(ipaddress.ip_address(self.broadcast), ipaddress.IPv4Address):
            raise ValueError("WOL_BROADCAST_ADDRESS must be an IPv4 address.")
        ipaddress.ip_address(self.host)
        if not 1 <= self.port <= 65535:
            raise ValueError("WOL_PORT must be between 1 and 65535.")

    @classmethod
    def from_env(cls):
        return cls(
            target_mac=os.getenv("WOL_TARGET_MAC", ""), token=os.getenv("WOL_API_TOKEN", ""),
            broadcast=os.getenv("WOL_BROADCAST_ADDRESS", "255.255.255.255"),
            host=os.getenv("WOL_BIND_HOST", "127.0.0.1"), port=int(os.getenv("WOL_PORT", "5000")),
        )


def create_app(settings: Settings | None = None, runner=None) -> Flask:
    load_dotenv()
    settings = settings or Settings.from_env()
    runner = runner or subprocess.run
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=1024, WOL_HOST=settings.host, WOL_PORT=settings.port)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/wol")
    def wake():
        authorization = request.headers.get("Authorization", "")
        supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
        if not hmac.compare_digest(supplied.encode("utf-8"), settings.token.encode("utf-8")):
            return jsonify(error="Unauthorized"), 401
        try:
            runner(["wakeonlan", "-i", settings.broadcast, settings.target_mac],
                   check=True, capture_output=True, timeout=5)
        except FileNotFoundError:
            return jsonify(error="The wakeonlan command is not installed on this server."), 503
        except subprocess.TimeoutExpired:
            return jsonify(error="The wake command timed out."), 504
        except (subprocess.CalledProcessError, OSError):
            return jsonify(error="The wake command failed. Check the server configuration."), 502
        return jsonify(status="sent", message="Magic packet sent; PC startup is not confirmed.")

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host=application.config["WOL_HOST"], port=application.config["WOL_PORT"])
