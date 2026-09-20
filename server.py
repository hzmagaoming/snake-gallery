#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""突发事件模拟仿真游戏 · 课堂作品集服务器

仅使用 Python 标准库：
  - 静态文件服务（index.html / games/ / assets/ ...）
  - GET  /api/likes         返回全部点赞数据
  - POST /api/like          body: {"game_id": "..."}  为指定游戏 +1 赞
"""
import json
import os
import socket
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LIKES_FILE = os.path.join(DATA_DIR, "likes.json")
PORT = 8000

_lock = threading.Lock()


def load_likes():
    with _lock:
        if not os.path.exists(LIKES_FILE):
            return {}
        try:
            with open(LIKES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}


def save_likes(likes):
    with _lock:
        tmp = LIKES_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(likes, f, ensure_ascii=False, indent=2)
        os.replace(tmp, LIKES_FILE)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, fmt, *args):  # 保持终端安静
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/likes":
            self._send_json(load_likes())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/like":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            game_id = str(payload.get("game_id", "")).strip()
        except (ValueError, json.JSONDecodeError):
            self._send_json({"error": "bad request"}, 400)
            return
        if not game_id or len(game_id) > 100:
            self._send_json({"error": "invalid game_id"}, 400)
            return
        likes = load_likes()
        likes[game_id] = int(likes.get(game_id, 0)) + 1
        save_likes(likes)
        self._send_json({"game_id": game_id, "likes": likes[game_id]})


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LIKES_FILE):
        save_likes({})
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("=" * 52)
    print("  突发事件模拟仿真游戏 · 课堂作品集")
    print("=" * 52)
    print(f"  本机访问:   http://localhost:{PORT}")
    print(f"  同学访问:   http://{lan_ip()}:{PORT}   (需同一 Wi-Fi)")
    print("  按 Ctrl+C 停止服务器")
    print("=" * 52)
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")


if __name__ == "__main__":
    main()
