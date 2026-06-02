"""Masterblog API — Flask backend exposing CRUD + search on blog posts.

A small JSON-file-backed REST API. Five endpoints under ``/api/posts``
(list with optional sort, create, delete, partial update, substring
search), JSON 404 / 405 error handlers and CORS enabled for the
frontend that runs on a separate port.
"""
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

POSTS_FILE = os.path.join(os.path.dirname(__file__), 'posts.json')


def load_posts():
    """Return the list of posts from disk, seeding two defaults if missing.

    Returns ``[]`` when the file exists but is unreadable / malformed.
    """
    if not os.path.exists(POSTS_FILE):
        default = [
            {"id": 1, "title": "First post", "content": "This is the first post."},
            {"id": 2, "title": "Second post", "content": "This is the second post."},
        ]
        save_posts(default)
        return default
    try:
        with open(POSTS_FILE, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_posts(posts):
    """Overwrite ``posts.json`` with ``posts`` (UTF-8, indented, no ASCII escape)."""
    with open(POSTS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(posts, handle, indent=2, ensure_ascii=False)


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """List all posts, optionally sorted by ``title`` or ``content``.

    Query params:
        sort: ``title`` or ``content`` (optional)
        direction: ``asc`` (default) or ``desc``

    Returns 400 on an invalid sort field or direction, 200 with the
    list otherwise.
    """
    posts = load_posts()
    sort_field = request.args.get('sort')
    direction = request.args.get('direction', 'asc')
    if sort_field:
        if sort_field not in ('title', 'content'):
            return jsonify({
                "error": "Invalid sort field. Use 'title' or 'content'."
            }), 400
        if direction not in ('asc', 'desc'):
            return jsonify({
                "error": "Invalid direction. Use 'asc' or 'desc'."
            }), 400
        posts = sorted(
            posts,
            key=lambda p: p[sort_field].lower(),
            reverse=(direction == 'desc'),
        )
    return jsonify(posts), 200


@app.route('/api/posts', methods=['POST'])
def add_post():
    """Create a new post.

    Body must be JSON with non-empty ``title`` and ``content``. Returns
    400 with a ``missing fields`` list when either is absent, otherwise
    201 with the newly created post (auto-incremented id).
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    missing = []
    if not data.get('title'):
        missing.append('title')
    if not data.get('content'):
        missing.append('content')
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    posts = load_posts()
    new_id = max([p['id'] for p in posts], default=0) + 1
    new_post = {
        "id": new_id,
        "title": data['title'].strip(),
        "content": data['content'].strip(),
    }
    posts.append(new_post)
    save_posts(posts)
    return jsonify(new_post), 201


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete the post with ``post_id``.

    Returns 404 when the id is unknown, 200 with a success message
    otherwise.
    """
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404
    posts = [p for p in posts if p['id'] != post_id]
    save_posts(posts)
    return jsonify({
        "message": f"Post with id {post_id} has been deleted successfully."
    }), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Partial-update the title and/or content of an existing post.

    Returns 404 when the id is unknown, 200 with the updated post
    otherwise. Either field may be omitted.
    """
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404
    data = request.get_json() or {}
    if 'title' in data:
        post['title'] = data['title'].strip()
    if 'content' in data:
        post['content'] = data['content'].strip()
    save_posts(posts)
    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """Case-insensitive substring search across title and/or content.

    Query params:
        title: substring to look for in the title (optional)
        content: substring to look for in the content (optional)

    A post matches when its title contains ``title`` OR its content
    contains ``content``. Empty query params are ignored.
    """
    title_q = request.args.get('title', '').lower()
    content_q = request.args.get('content', '').lower()
    posts = load_posts()
    results = [
        post for post in posts
        if (title_q and title_q in post['title'].lower())
        or (content_q and content_q in post['content'].lower())
    ]
    return jsonify(results), 200


@app.errorhandler(404)
def not_found(error):
    """Return a JSON body for unmatched routes instead of HTML."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Return a JSON body for method-not-allowed instead of HTML."""
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
