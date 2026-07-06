from flask import Flask
from flask_sock import Sock
from queue import Queue
import threading, json, os, uuid, hmac
from datetime import datetime, UTC

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
sock = Sock(app)
clients = {}
clients_lock = threading.Lock()
queue = Queue(maxsize=1000)
TOKEN = os.getenv("API_TOKEN")
if not TOKEN:
    raise RuntimeError("API_TOKEN environment variable must be set")


def enqueue_event(source, channel, payload):
    """Normalize and enqueue an event for websocket delivery."""
    event_payload = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "source": source,
        "channel": channel,
        **payload,
    }
    queue.put_nowait((channel, event_payload))
    return event_payload


def dispatcher():
    """Dispatch queued events to connected websocket clients."""
    while True:
        channel, payload = queue.get()
        dead = []
        with clients_lock:
            receivers = list(clients.get(channel, set()))
        for ws in receivers:
            try:
                ws.send(json.dumps(payload))
            except Exception:
                dead.append(ws)
        if dead:
            with clients_lock:
                for ws in dead:
                    clients.get(channel, set()).discard(ws)


def auth(request):
    """Validate the Bearer token from the Authorization header."""
    auth_hdr = request.headers.get("Authorization", "")
    expected = f"Bearer {TOKEN}"
    return hmac.compare_digest(auth_hdr, expected)


threading.Thread(target=dispatcher, daemon=True).start()
