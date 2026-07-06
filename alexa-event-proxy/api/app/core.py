from flask import Flask
from flask_sock import Sock
from queue import Queue
import threading, json, os, uuid
from datetime import datetime, UTC

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
sock = Sock(app)
clients = {}
clients_lock = threading.Lock()
queue = Queue(maxsize=1000)


def enqueue_event(source, channel, payload):
    """Normalize and enqueue an event for websocket delivery."""
    event_payload = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "source": source,
        "channel": channel,
        "payload": payload if isinstance(payload, dict) else {},
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


threading.Thread(target=dispatcher, daemon=True).start()
