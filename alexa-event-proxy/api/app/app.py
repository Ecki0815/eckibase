from flask import Flask, request, jsonify
from flask_sock import Sock
from queue import Queue, Full
import threading, json, os, uuid, hmac
from datetime import datetime, UTC

app = Flask(__name__)
# limit request size to 1 MiB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
sock = Sock(app)
clients = {}
clients_lock = threading.Lock()
# bounded queue to reduce DoS risk
queue = Queue(maxsize=1000)
TOKEN = os.getenv("API_TOKEN")
if not TOKEN:
    raise RuntimeError("API_TOKEN environment variable must be set")

def dispatcher():
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
                    
thread=threading.Thread(target=dispatcher,daemon=True).start()

def auth():
    auth_hdr = request.headers.get("Authorization", "")
    expected = f"Bearer {TOKEN}"
    return hmac.compare_digest(auth_hdr, expected)

@app.get("/health")
def health():
    return {"status":"ok","clients":sum(len(v) for v in clients.values())}

@app.post("/api/v1/event")
def event():
    if not auth():
        return {"error":"unauthorized"},401
    data = request.get_json(force=True)
    if not isinstance(data, dict):
        return {"error": "invalid_payload"}, 400
    ch = data.pop("channel", "default")
    data["id"] = str(uuid.uuid4())
    data["timestamp"] = datetime.now(UTC).isoformat()
    try:
        queue.put_nowait((ch, data))
    except Full:
        return {"error": "server_busy"}, 429
    return {"success": True}

@sock.route("/ws")
def ws(ws):
    auth_hdr = request.headers.get("Authorization", "")
    expected = f"Bearer {TOKEN}"
    if not hmac.compare_digest(auth_hdr, expected):
        try:
            ws.close()
        except Exception:
            pass
        return
    ch = request.args.get("channel", "default")
    with clients_lock:
        clients.setdefault(ch, set()).add(ws)
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
            if msg == "ping":
                ws.send("pong")
    finally:
        with clients_lock:
            clients.get(ch, set()).discard(ws)
