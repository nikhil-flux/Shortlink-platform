"""Shortlink: a tiny URL shortener with Redis storage and Prometheus metrics."""
import os
import secrets
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REDIS_URL = os.getenv("REDIS_URL", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

REQUESTS = Counter("shortlink_requests_total", "HTTP requests", ["endpoint", "status"])
LATENCY = Histogram("shortlink_request_seconds", "Request latency", ["endpoint"])
CREATED = Counter("shortlink_created_total", "Short links created")
REDIRECTS = Counter("shortlink_redirects_total", "Redirects served")


class MemoryStore:
    """Fallback store used in tests and when REDIS_URL is not set."""

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def ping(self):
        return True


def make_store():
    if not REDIS_URL:
        return MemoryStore()
    import redis

    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    class RedisStore:
        def get(self, key):
            return client.get(key)

        def set(self, key, value):
            client.set(key, value)

        def ping(self):
            return client.ping()

    return RedisStore()


def create_app(store=None):
    app = Flask(__name__)
    app.config["store"] = store or make_store()

    def valid_url(value):
        parsed = urlparse(value or "")
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/readyz")
    def readyz():
        try:
            app.config["store"].ping()
        except Exception:
            return jsonify(status="store unavailable"), 503
        return jsonify(status="ready")

    @app.post("/api/shorten")
    @LATENCY.labels("shorten").time()
    def shorten():
        url = (request.get_json(silent=True) or {}).get("url")
        if not valid_url(url):
            REQUESTS.labels("shorten", "400").inc()
            return jsonify(error="a valid http(s) url is required"), 400
        code = secrets.token_urlsafe(5)
        app.config["store"].set(code, url)
        CREATED.inc()
        REQUESTS.labels("shorten", "201").inc()
        return jsonify(code=code, short_url=f"{BASE_URL}/{code}"), 201

    @app.get("/<code>")
    @LATENCY.labels("redirect").time()
    def follow(code):
        url = app.config["store"].get(code)
        if not url:
            REQUESTS.labels("redirect", "404").inc()
            return jsonify(error="not found"), 404
        REDIRECTS.inc()
        REQUESTS.labels("redirect", "302").inc()
        return redirect(url, code=302)

    @app.get("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app


app = create_app()
