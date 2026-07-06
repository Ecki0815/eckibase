import json
from flask import jsonify, request
from .core import app, auth, enqueue_event, clients, clients_lock, sock
from .adapters import register_adapters

register_adapters(app)


@app.get("/health")
def health():
    """Health-check endpoint reporting uptime status and active websocket clients."""
    return jsonify({"status": "ok", "clients": sum(len(v) for v in clients.values())})


@app.post("/api/v1/event")
def event():
    """Generic event ingestion endpoint.

    Accepts arbitrary JSON events and sends them into the proxy event bus.
    """
    if not auth(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid_payload"}), 400

    source = data.pop("source", "generic")
    channel = data.pop("channel", "default")
    enqueue_event(source, channel, data)
    return jsonify({"success": True, "channel": channel, "source": source})


@sock.route("/ws")
def websocket_route(ws):
    """Websocket endpoint for subscribing to proxy event channels."""
    if not auth(request):
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
                continue
            try:
                payload = json.loads(msg)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            source = payload.get("source", "ws")
            channel = payload.get("channel", ch)
            event_payload = payload.get("payload") or {}
            if not isinstance(event_payload, dict):
                continue
            enqueue_event(source, channel, event_payload)
    finally:
        with clients_lock:
            clients.get(ch, set()).discard(ws)
