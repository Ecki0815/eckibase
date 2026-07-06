import json
import os
import uuid
from datetime import datetime, UTC
from flask import jsonify, request
from ..core import enqueue_event, auth


def get_alexa_devices():
    raw_devices = os.getenv("ALEXA_DEVICES", "[]")
    try:
        devices = json.loads(raw_devices)
    except Exception:
        devices = []

    if not isinstance(devices, list):
        devices = []

    if not devices:
        devices = [{
            "endpointId": "generic-proxy-endpoint",
            "friendlyName": "Generic Event Bridge",
            "description": "Generic bridge for voice-controlled devices",
            "entity_id": None,
            "device_type": "switch",
        }]

    normalized = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        endpoint_id = device.get("endpointId") or device.get("id") or f"device-{len(normalized) + 1}"
        normalized.append({
            "endpointId": endpoint_id,
            "friendlyName": device.get("friendlyName") or device.get("name") or endpoint_id,
            "description": device.get("description") or "Voice-controlled device",
            "entity_id": device.get("entity_id"),
            "device_type": device.get("device_type", "switch"),
        })

    return normalized


def build_alexa_endpoint(device):
    return {
        "endpointId": device["endpointId"],
        "manufacturerName": "eckibase",
        "friendlyName": device["friendlyName"],
        "description": device["description"],
        "displayCategories": ["SWITCH"],
        "capabilities": [
            {"type": "AlexaInterface", "interface": "Alexa", "version": "3"},
            {"type": "AlexaInterface", "interface": "Alexa.PowerController", "version": "3"},
        ],
    }


def register_routes(app):
    @app.post("/api/v1/adapters/alexa")
    def alexa_adapter():
        if not auth(request):
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        directive = data.get("directive") or {}
        header = directive.get("header") or {}
        payload = directive.get("payload") or {}

        message_id = header.get("messageId") or str(uuid.uuid4())
        namespace = header.get("namespace", "")
        name = header.get("name", "")
        endpoint_id = (payload.get("endpoint") or {}).get("endpointId") or "generic-proxy-endpoint"

        if namespace == "Alexa.Discovery" and name == "Discover":
            devices = get_alexa_devices()
            response = {
                "event": {
                    "header": {
                        "messageId": message_id,
                        "namespace": "Alexa.Discovery",
                        "name": "Discover.Response",
                        "payloadVersion": "3",
                    },
                    "payload": {
                        "endpoints": [build_alexa_endpoint(device) for device in devices]
                    },
                }
            }
            enqueue_event("alexa", "alexa", {"action": "discover", "devices": [device["endpointId"] for device in devices]})
            return jsonify(response)

        if namespace == "Alexa.PowerController" and name in {"TurnOn", "TurnOff"}:
            state = "ON" if name == "TurnOn" else "OFF"
            devices = get_alexa_devices()
            device = next((item for item in devices if item["endpointId"] == endpoint_id), None)
            entity_id = device.get("entity_id") if device else None
            ha_channel = os.getenv("HA_CHANNEL", "homeassistant")
            enqueue_event(
                "alexa",
                ha_channel,
                {
                    "action": name.lower(),
                    "endpoint_id": endpoint_id,
                    "state": state,
                    "entity_id": entity_id,
                },
            )
            return jsonify({
                "event": {
                    "header": {
                        "messageId": message_id,
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                    },
                    "endpoint": {"endpointId": endpoint_id},
                    "payload": {},
                },
                "context": {
                    "properties": [{
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": state,
                        "timeOfSample": datetime.now(UTC).isoformat(),
                        "uncertaintyInMilliseconds": 0,
                    }]
                },
            })

        return jsonify({
            "event": {
                "header": {
                    "messageId": message_id,
                    "namespace": "Alexa",
                    "name": "ErrorResponse",
                    "payloadVersion": "3",
                },
                "endpoint": {"endpointId": endpoint_id},
                "payload": {"type": "INVALID_DIRECTIVE", "message": "unsupported directive"},
            }
        }), 400
