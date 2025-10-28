#!/usr/bin/env python3
"""
YouTube Music Discord RPC Server (Complete English Version)
Features:
- Fetches YouTube thumbnail dynamically for the cover.
- Status: "Listening to <title>".
- Two buttons: "Listen on YouTube" and "GitHub".
- Curses-based tiling CLI dashboard.
- Runs in background with --daemon (Unix).
- Thread-safe, resilient RPC reconnection.
"""

import os
import re
import sys
import time
import json
import argparse
import logging
import threading
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from pypresence import Presence
except ImportError:
    Presence = None

# ---------- CONFIG ----------
CLIENT_ID = "[YOURCLIENTID]"
GITHUB_URL = "https://github.com/louchatfroff  # Dont replace, Credit
HOST = "localhost"
PORT = 8765
PIDFILE = "/tmp/ytm_rpc_server.pid"

# ---------- GLOBALS ----------
app = Flask(__name__)
CORS(app)
rpc = None
rpc_connected = False
current_music = None
last_attempt = 0
rpc_lock = threading.Lock()


# ---------- LOGGING ----------
def setup_logging(verbose=False, log_file=None):
    fmt = "[%(asctime)s] %(levelname)s: %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format=fmt, handlers=handlers)


# ---------- UTILITIES ----------
def extract_thumbnail(url: str):
    """Extract thumbnail from YouTube URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", str(url))
    if not match:
        return None
    vid = match.group(1)
    return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"


def is_posix():
    return os.name == "posix"


def daemonize(pidfile=PIDFILE):
    """Run process as background daemon on Unix systems."""
    if not is_posix():
        logging.warning("Daemon mode only works on Unix-like systems.")
        return False
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        logging.error(f"First fork failed: {e}")
        return False
    os.chdir("/")
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        logging.error(f"Second fork failed: {e}")
        return False
    sys.stdout.flush()
    sys.stderr.flush()
    with open("/dev/null", "rb", 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(pidfile, "w") as f:
        f.write(str(os.getpid()))
    return True


# ---------- DISCORD RPC ----------
def connect_discord(force=False):
    """Establish or reestablish RPC connection."""
    global rpc, rpc_connected, last_attempt
    with rpc_lock:
        if not force and rpc_connected:
            return True
        now = time.time()
        if now - last_attempt < 5:
            return False
        last_attempt = now
        if rpc:
            try:
                rpc.close()
            except Exception:
                pass
            rpc = None
        if not Presence:
            logging.warning("pypresence not installed; skipping RPC.")
            return False
        try:
            rpc = Presence(CLIENT_ID)
            rpc.connect()
            rpc_connected = True
            logging.info("Connected to Discord RPC.")
            return True
        except Exception as e:
            logging.error(f"RPC connection failed: {e}")
            rpc_connected = False
            return False


def update_presence():
    """Push updated presence to Discord."""
    global rpc_connected, rpc, current_music
    if not rpc_connected and not connect_discord():
        return
    if not current_music:
        return
    try:
        title = current_music.get("title", "Unknown")
        artist = current_music.get("artist", "Unknown")
        url = current_music.get("url")
        paused = bool(current_music.get("isPaused", False))
        elapsed = float(current_music.get("currentTime", 0))
        duration = float(current_music.get("duration", 0))
        thumb = extract_thumbnail(url) if url else "youtube_music_logo"

        data = {
            "details": f"Listening to {title}",
            "state": f"by {artist}",
            "large_image": thumb,
            "large_text": title,
            "small_image": "pause" if paused else "play",
            "small_text": "Paused" if paused else "Playing",
        }

        if not paused and duration > 0:
            now = time.time()
            data["start"] = int(now - elapsed)
            data["end"] = int(now + (duration - elapsed))

        buttons = [{"label": "GitHub", "url": GITHUB_URL}]
        if url:
            buttons.insert(0, {"label": "Listen on YouTube", "url": url})
        data["buttons"] = buttons

        with rpc_lock:
            rpc.update(**data)
        logging.info(f"Presence updated: {title}")

    except Exception as e:
        logging.error(f"Presence update failed: {e}")
        rpc_connected = False
        connect_discord(force=True)


# ---------- FLASK ROUTES ----------
@app.route("/update", methods=["POST"])
def update():
    global current_music
    try:
        current_music = request.get_json()
        threading.Thread(target=update_presence, daemon=True).start()
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error(f"/update error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/clear", methods=["POST"])
def clear():
    global current_music
    try:
        if rpc and rpc_connected:
            with rpc_lock:
                rpc.clear()
        current_music = None
        logging.info("Presence cleared.")
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error(f"/clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"connected": rpc_connected, "timestamp": time.time()})


# ---------- MAINTENANCE THREADS ----------
def rpc_watchdog():
    while True:
        time.sleep(10)
        if not rpc_connected:
            connect_discord(force=True)


def keep_alive():
    while True:
        time.sleep(15)
        if rpc_connected and current_music and not current_music.get("isPaused", False):
            update_presence()


# ---------- CURSES CLI ----------
def run_tui(stop_event):
    try:
        import curses
    except Exception:
        logging.warning("Curses not available, skipping TUI.")
        return

    def draw(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        while not stop_event.is_set():
            stdscr.erase()
            maxy, maxx = stdscr.getmaxyx()
            split = maxx // 3
            left = stdscr.subwin(maxy, split, 0, 0)
            left.box()
            left.addstr(1, 2, "Server Status")
            left.addstr(3, 2, f"RPC connected: {rpc_connected}")
            left.addstr(4, 2, f"Host: {HOST}:{PORT}")
            left.addstr(5, 2, f"PID: {os.getpid()}")

            right = stdscr.subwin(maxy, maxx - split, 0, split)
            right.box()
            right.addstr(1, 2, "Now Playing")
            if current_music:
                right.addstr(3, 2, f"Title: {current_music.get('title', 'Unknown')}")
                right.addstr(4, 2, f"Artist: {current_music.get('artist', 'Unknown')}")
                if current_music.get('url'):
                    right.addstr(6, 2, f"URL: {current_music.get('url')[:maxx - split - 6]}")
                right.addstr(8, 2, f"Paused: {current_music.get('isPaused', False)}")
            else:
                right.addstr(3, 2, "No song data yet.")
            stdscr.refresh()
            time.sleep(0.5)

    curses.wrapper(draw)


# ---------- MAIN ----------
def start_server(gui=True, daemon=False, log_file=None, verbose=False):
    setup_logging(verbose, log_file)
    logging.info("Starting YouTube Music Discord RPC Server.")
    if daemon and is_posix():
        daemonize()
        logging.info("Running in background (daemon).")
    connect_discord()
    threading.Thread(target=rpc_watchdog, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    tui_stop = threading.Event()
    if gui and not daemon:
        threading.Thread(target=run_tui, args=(tui_stop,), daemon=True).start()
    else:
        logging.info("TUI disabled.")

    try:
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        tui_stop.set()
        logging.info("Shutting down.")
        if os.path.exists(PIDFILE):
            os.remove(PIDFILE)


def parse_args():
    p = argparse.ArgumentParser(description="YouTube Music Discord RPC Server (Complete)")
    p.add_argument("--no-gui", action="store_true", help="Disable curses interface.")
    p.add_argument("--daemon", action="store_true", help="Run as background daemon (Unix).")
    p.add_argument("--log", type=str, help="Path to log file.")
    p.add_argument("--verbose", action="store_true", help="Verbose output.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    start_server(gui=not args.no_gui, daemon=args.daemon, log_file=args.log, verbose=args.verbose)
