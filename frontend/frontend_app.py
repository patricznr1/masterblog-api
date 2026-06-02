"""Masterblog API frontend — minimal Flask app serving ``index.html``.

Runs on a different port than the backend (default 5001 vs. 5002).
The page itself uses fetch() to call the backend.
"""
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    """Render the single-page UI."""
    return render_template("index.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
