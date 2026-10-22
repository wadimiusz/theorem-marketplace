from pathlib import Path

import yaml

COMPOSE = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "docker-compose.yml").read_text()
)

# Every published port must be listed here. Docker bypasses UFW, so a port bound to
# 0.0.0.0 is public, and app.py trusts X-Forwarded-For (ProxyFix x_for=1), which is
# only safe while nothing but the host's nginx can connect to gunicorn.
ALLOWED_PORTS = {"theorem-marketplace": ["127.0.0.1:5000:5000"]}


def test_allowed_ports_are_localhost_only():
    for ports in ALLOWED_PORTS.values():
        assert all(port.startswith("127.0.0.1:") for port in ports)


def test_only_allowlisted_ports_are_published():
    for name, service in COMPOSE["services"].items():
        assert service.get("ports", []) == ALLOWED_PORTS.get(name, []), name
