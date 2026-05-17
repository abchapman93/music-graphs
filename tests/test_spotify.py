import pytest

from lib.spotify import SPOTIFY_KINDS, spotify_embed_url


def test_spotify_kinds_contents():
    assert SPOTIFY_KINDS == frozenset(
        {"track", "album", "playlist", "artist", "episode", "show"}
    )


def test_track_with_query_string():
    assert (
        spotify_embed_url("https://open.spotify.com/track/abc123?si=xyz")
        == "https://open.spotify.com/embed/track/abc123"
    )


@pytest.mark.parametrize(
    "kind",
    ["album", "playlist", "artist", "episode", "show"],
)
def test_other_kinds(kind):
    assert (
        spotify_embed_url(f"https://open.spotify.com/{kind}/abc123")
        == f"https://open.spotify.com/embed/{kind}/abc123"
    )


def test_http_input_becomes_https():
    assert (
        spotify_embed_url("http://open.spotify.com/track/abc123")
        == "https://open.spotify.com/embed/track/abc123"
    )


def test_trailing_slash_stripped():
    assert (
        spotify_embed_url("https://open.spotify.com/track/abc123/")
        == "https://open.spotify.com/embed/track/abc123"
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "not a url",
        "https://example.com/track/xyz",
        "https://open.spotify.com/unknown/xyz",
        "https://open.spotify.com/track/",
        "https://open.spotify.com/track",
        "ftp://open.spotify.com/track/abc",
    ],
)
def test_bad_inputs_return_none(bad):
    assert spotify_embed_url(bad) is None
