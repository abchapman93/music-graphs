"""Smoke test for the Flask app skeleton."""

import os
import sys

# Make the project root importable when pytest is invoked from anywhere.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app  # noqa: E402


def test_home_returns_200():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_home_lists_stub_graphs():
    client = app.test_client()
    body = client.get("/").get_data(as_text=True)
    assert "pittsburgh-jazz" in body
    assert "band-x" in body
    assert "bowie-covers" in body


def test_stub_routes_return_501():
    client = app.test_client()
    assert client.get("/graph/foo").status_code == 501
    assert client.get("/api/graph/foo").status_code == 501
    assert client.get("/api/card/foo/bar").status_code == 501
    assert client.get("/graph/foo/card/bar").status_code == 501
    assert client.get("/cards").status_code == 501
