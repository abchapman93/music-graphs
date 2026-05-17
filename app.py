"""music-graphs Flask app skeleton.

Phase 1, Track A: serves a home page listing stub graphs and reserves the
URL shape for routes that later waves will fill in.
"""

from flask import Flask, render_template

app = Flask(__name__)

# Hard-coded stub graphs so the home page is visually populated in Phase 1.
# Wave 2 will replace this with discovery from the cards directory.
STUB_GRAPHS = [
    {
        "slug": "pittsburgh-jazz",
        "name": "Pittsburgh Jazz",
        "description": "Placeholder: musicians, venues, and recordings from the Pittsburgh jazz scene.",
    },
    {
        "slug": "band-x",
        "name": "Band X",
        "description": "Placeholder: members, side projects, and influences.",
    },
    {
        "slug": "bowie-covers",
        "name": "Bowie Covers",
        "description": "Placeholder: notable covers of David Bowie songs.",
    },
]


@app.route("/")
def home():
    return render_template("home.html", graphs=STUB_GRAPHS)


# --- Wave 2/3 route stubs ---------------------------------------------------
# These lock URL shapes so later tracks can fill them in without renaming.

@app.route("/graph/<slug>")
def graph_view(slug):
    return ("not implemented", 501)


@app.route("/api/graph/<slug>")
def api_graph(slug):
    return ("not implemented", 501)


@app.route("/api/card/<graph_slug>/<card_slug>")
def api_card(graph_slug, card_slug):
    return ("not implemented", 501)


@app.route("/graph/<slug>/card/<card_slug>")
def card_view(slug, card_slug):
    return ("not implemented", 501)


@app.route("/cards")
def cards_index():
    return ("not implemented", 501)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8766, debug=True)
