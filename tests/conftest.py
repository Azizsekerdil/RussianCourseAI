# -*- coding: utf-8 -*-
"""Ortak test altyapisi.

- Gizli anahtar deposu her testte DOSYA arka ucuna zorlanir; gercek Windows
  Credential Manager'a hicbir test dokunmaz.
- `mock_server`: OpenAI uyumlu sahte sunucu (GET /v1/models, POST /v1/chat/completions).
  Authorization basligini ve istek govdesini kaydeder; hicbir test gercek aga cikmaz.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RUSSIANCOURSEAI_SECRETS_FILE", "1")
os.environ.pop("RUSSIANCOURSEAI_API_KEY", None)

# Kod citi icinde JSON dizisi: cit temizleme yolunu da sinar.
DEFAULT_CONTENT = (
    "```json\n"
    "[\n"
    '  {"headword": "приве\'т", "pos": "int", "extra": "", "translation": "hi; hello",\n'
    '   "example": "Привет, как дела?", "note": "Informal greeting between friends."},\n'
    '  {"headword": "здра\'вствуйте", "pos": "int", "extra": "",\n'
    '   "translation": "hello (formal)", "example": "Здравствуйте, меня зовут Анна.",\n'
    '   "note": "Formal or plural greeting."}\n'
    "]\n"
    "```"
)


def free_port() -> int:
    """Kapali (dinlenmeyen) bir yerel port numarasi."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class MockOpenAIServer:
    """OpenAI uyumlu sahte sunucu (arka plan thread'inde calisir)."""

    def __init__(self) -> None:
        self.requests: list = []
        self.content = DEFAULT_CONTENT
        self.model_ids = ["mock-model"]
        self.delay = 0.0            # sohbet yaniti bu kadar saniye geciktirilir (yaris testleri)
        self.lock = threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_a) -> None:          # sessiz
                pass

            def _send(self, code: int, payload: dict) -> None:
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                outer._record(self, b"")
                if self.path.rstrip("/").endswith("/v1/models"):
                    self._send(200, {"object": "list",
                                     "data": [{"id": m, "object": "model"} for m in outer.model_ids]})
                else:
                    self._send(404, {"error": "not found"})

            def do_POST(self) -> None:
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else b""
                outer._record(self, body)
                if self.path.rstrip("/").endswith("/v1/chat/completions"):
                    try:
                        req = json.loads(body.decode("utf-8"))
                    except Exception:                       # noqa: BLE001
                        req = {}
                    if outer.delay:
                        time.sleep(outer.delay)
                    self._send(200, {
                        "id": "chatcmpl-mock", "object": "chat.completion",
                        "model": req.get("model", "mock-model"),
                        "choices": [{"index": 0, "finish_reason": "stop",
                                     "message": {"role": "assistant", "content": outer.content}}],
                        "usage": {"prompt_tokens": 42, "completion_tokens": 21, "total_tokens": 63},
                    })
                else:
                    self._send(404, {"error": "not found"})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = int(self.httpd.server_address[1])
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def _record(self, handler, body: bytes) -> None:
        with self.lock:
            self.requests.append({"method": handler.command, "path": handler.path,
                                  "auth": handler.headers.get("Authorization", ""),
                                  "body": body.decode("utf-8", "replace")})

    @property
    def count(self) -> int:
        with self.lock:
            return len(self.requests)

    def chat_requests(self) -> list:
        with self.lock:
            return [r for r in self.requests if "chat/completions" in r["path"]]

    def model_requests(self) -> list:
        with self.lock:
            return [r for r in self.requests if r["path"].rstrip("/").endswith("/v1/models")]

    def reset(self) -> None:
        with self.lock:
            self.requests.clear()
        self.content = DEFAULT_CONTENT
        self.model_ids = ["mock-model"]
        self.delay = 0.0

    def close(self) -> None:
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
        except Exception:                                   # noqa: BLE001
            pass


@pytest.fixture(scope="session")
def mock_server():
    srv = MockOpenAIServer()
    yield srv
    srv.close()
