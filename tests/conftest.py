import os
import sys

import pytest

# app.py reads these at import time; tests never touch the DB or the chain.
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("HTTP_PROVIDER", "http://127.0.0.1:1")
os.environ.setdefault("CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app  # noqa: E402
from app import limiter  # noqa: E402

# In production every request reaches gunicorn from the docker bridge gateway.
DOCKER_GATEWAY = "172.18.0.1"


@pytest.fixture
def client():
    limiter.reset()
    return flask_app.test_client()


@pytest.fixture
def get_as(client):
    """GET a path as if nginx proxied it on behalf of the given X-Forwarded-For chain."""

    def _get(path, xff):
        return client.get(
            path,
            environ_base={"REMOTE_ADDR": DOCKER_GATEWAY},
            headers={"X-Forwarded-For": xff},
        )

    return _get
