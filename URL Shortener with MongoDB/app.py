from flask import Flask, jsonify, request, redirect
from pymongo import MongoClient
import os
import string
import random

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "mongodb-0.mongodb-headless,mongodb-1.mongodb-headless,mongodb-2.mongodb-headless")
DB_NAME = os.environ.get("DB_NAME", "urlshortener")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

uri = f"mongodb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:27017/{DB_NAME}?replicaSet=rs0&authSource=admin"
client = MongoClient(uri)
db = client[DB_NAME]
urls = db["urls"]


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    long_url = data.get("url")
    if not long_url:
        return jsonify({"error": "url is required"}), 400

    short_code = generate_short_code()
    urls.insert_one({"short_code": short_code, "long_url": long_url, "clicks": 0})

    return jsonify({"short_code": short_code, "long_url": long_url}), 201


@app.route("/<short_code>")
def redirect_to_url(short_code):
    entry = urls.find_one({"short_code": short_code})
    if not entry:
        return jsonify({"error": "short URL not found"}), 404

    urls.update_one({"short_code": short_code}, {"$inc": {"clicks": 1}})
    return redirect(entry["long_url"])


@app.route("/stats/<short_code>")
def stats(short_code):
    entry = urls.find_one({"short_code": short_code})
    if not entry:
        return jsonify({"error": "short URL not found"}), 404

    return jsonify({
        "short_code": entry["short_code"],
        "long_url": entry["long_url"],
        "clicks": entry["clicks"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)