"""Smoke test for the Flask app."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app  # noqa: E402


def test_home_returns_200():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_cards_index_returns_200():
    # Track G implements this; the page lists every card across graphs.
    client = app.test_client()
    assert client.get("/cards").status_code == 200
