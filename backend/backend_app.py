from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

POSTS_FILE = os.path.join(os.path.dirname(__file__), 'posts.json')


def load_posts():
    if not os.path.exists(POSTS_FILE):
        default = [
            {"id": 1, "title": "First post", "content": "This is the first post."},
            {"id": 2, "title": "Second post", "content": "This is the second post."},
        ]
        save_posts(default)
        return default
    try:
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = load_posts()
    sort_field = request.args.get('sort')
    direction = request.args.get('direction', 'asc')
    if sort_field:
        if sort_field not in ('title', 'content'):
            return jsonify({"error": "Invalid sort field. Use 'title' or 'content'."}), 400
        if direction not in ('asc', 'desc'):
            return jsonify({"error": "Invalid direction. Use 'asc' or 'desc'."}), 400
        posts = sorted(posts, key=lambda p: p[sort_field].lower(), reverse=(direction == 'desc'))
    return jsonify(posts), 200


@app.route('/api/posts', methods=['POST'])
def add_post():
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
    new_post = {"id": new_id, "title": data['title'].strip(), "content": data['content'].strip()}
    posts.append(new_post)
    save_posts(posts)
    print(f" Neuer Post #{new_id} erstellt")
    return jsonify(new_post), 201


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404
    posts = [p for p in posts if p['id'] != post_id]
    save_posts(posts)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
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
    title_q = request.args.get('title', '').lower()
    content_q = request.args.get('content', '').lower()
    posts = load_posts()
    results = [p for p in posts if (title_q and title_q in p['title'].lower()) or (content_q and content_q in p['content'].lower())]
    return jsonify(results), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
