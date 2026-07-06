# Alexa Event Proxy

This project is an event proxy for Alexa and Home Assistant workflows, with a generic event bus for custom adapters.

## Architecture

The project is designed as a generic event bridge rather than as a single-purpose Alexa or Home Assistant integration.

### Core idea
The core service is responsible for three things:
1. Accepting authenticated events from any source.
2. Normalizing them into a simple internal event format.
3. Broadcasting them to subscribed channels over HTTP/WebSocket.

This means the proxy can handle events from Home Assistant, Alexa, or other custom services.

### Suggested architecture
The system is split into three layers:

1. Core proxy
   - Receives events through HTTP endpoints
   - Validates authentication
   - Stores events in an internal queue
   - Publishes them to channels
   - Exposes a websocket stream for listeners

2. Adapter layer
   - Adapters translate provider-specific payloads into the generic event format.
   - Examples:
     - Alexa adapter: converts Alexa directives into generic events and back into Alexa-compatible responses
     - custom services can publish to the proxy using the generic `/api/v1/event` endpoint
   - The adapter layer is intentionally separate so new integrations can be added without changing the core proxy.
   - In code, adapters live in `api/app/adapters/` and are registered by `api/app/app.py`.

3. Consumer layer
   - Consumers subscribe to channels and react to events.
   - This could be:
     - a websocket client
     - a Home Assistant automation
     - an Alexa skill handler
     - any other custom service

### Event shape
Every event is normalized into a common structure consisting of:
- `source`: where the event originated from
- `channel`: the logical topic or stream
- `payload`: the provider-specific payload
- `id`: a generated event id
- `timestamp`: a timestamp in UTC

This keeps the core simple and makes it easy to connect different systems with different message schemas.

### Why this design is useful
This architecture makes the project reusable for the Alexa + Home Assistant use case while still supporting additional adapters later:
- You can start with Alexa as the primary adapter.
- Later you can connect Home Assistant or other services without changing the core event flow.
- The proxy remains a generic endpoint for automation and local event delivery.

### Example flow
1. A source sends an event to `/api/v1/event` or connects via websocket.
2. The core proxy normalizes it into a generic event.
3. The proxy publishes it to a channel such as `homeassistant`.
4. A websocket client consumes that event and acts locally.
5. If needed, another adapter such as Alexa transforms the event into an Alexa-compatible response.

This approach gives you a clean separation between:
- transport
- protocol translation
- business logic
- consumer integration

## Important use case: Alexa voice control for Home Assistant

This project is already structured for the key use case you described:

1. Alexa discovers voice-controllable devices through the skill endpoint.
2. The Alexa skill forwards the command to the proxy.
3. The proxy forwards the command into the `homeassistant` channel.

### What is supported now
- Alexa can discover devices listed in the environment variable `ALEXA_DEVICES`.
- Alexa can handle `TurnOn` and `TurnOff` directives.
- If Home Assistant is not internet-reachable, it can connect as a websocket client to the proxy and receive commands on a private channel.
- Alexa commands can be sent to a Home Assistant WS channel via the proxy if `HA_CHANNEL` is configured.

### Configuration example
Set these environment variables in `.env`:

```dotenv
NGINX_AUTH_USER=proxyuser
NGINX_AUTH_PASSWORD=change_me
ALEXA_DEVICES=[{"endpointId":"switch.kitchen","friendlyName":"Kueche","entity_id":"switch.kitchen","device_type":"switch"}]
HA_CHANNEL=homeassistant
```

### Example Alexa discovery request
```bash
curl -X POST http://127.0.0.1:1558/api/v1/adapters/alexa \
  -H "Authorization: Basic <base64-credentials>" \
  -H "Content-Type: application/json" \
  -d '{"directive":{"header":{"namespace":"Alexa.Discovery","name":"Discover","messageId":"1"}}}'
```

### Example Alexa turn-on request
```bash
curl -X POST http://127.0.0.1:1558/api/v1/adapters/alexa \
  -H "Authorization: Basic <base64-credentials>" \
  -H "Content-Type: application/json" \
  -d '{"directive":{"header":{"namespace":"Alexa.PowerController","name":"TurnOn","messageId":"2"},"payload":{"endpoint":{"endpointId":"switch.kitchen"}}}}'
```

This is now a valid and useful end-to-end flow for voice-controlled devices.

## Core endpoints
- `POST /api/v1/event` – generic event ingestion
- `POST /api/v1/adapters/alexa` – Alexa adapter endpoint
- `GET /health` – health check
- `WS /ws` – websocket stream

## Function overview

### `enqueue_event(source, channel, payload)`
Normalizes incoming events by adding `id`, `timestamp`, `source`, and `channel`, then enqueues them for delivery to websocket clients.

### `dispatcher()`
Background worker that forwards queued events to all websocket clients subscribed to the event channel.

### `auth()`
No direct API token check is required; authentication is handled by Nginx Basic Auth upstream.

### `get_alexa_devices()`
Loads Alexa device definitions from the `ALEXA_DEVICES` environment variable and creates a normalized device list for discovery.

### `build_alexa_endpoint(device)`
Builds an Alexa discovery endpoint object from a normalized device definition.

### `health()`
Simple health endpoint returning service status and active websocket client count.

### `event()`
Generic event ingestion endpoint for arbitrary sources and channels. Useful for any integration that wants to publish into the event bus.

### `alexa_adapter()`
Alexa adapter endpoint handling device discovery and power control directives. It translates Alexa directives into proxy events for the configured channel.

### `ws(ws)`
Websocket endpoint for subscribing to realtime event channels.

## Websocket integration for Home Assistant
Home Assistant can connect outbound to `wss://<proxy>/ws?channel=homeassistant` and receive proxy events without exposing a public inbound webhook.

This is the recommended setup when HA is running behind a private network and should not open ports to the internet.

The HA websocket client should authenticate with Nginx using Basic Auth.

Once connected, Home Assistant can act as both:
- a consumer: receive proxy events on the `homeassistant` channel
- a producer: send messages into the proxy by transmitting JSON payloads over the same websocket

For the Alexa use case, the flow becomes:
1. Alexa sends a voice command to `/api/v1/adapters/alexa`.
2. The Alexa adapter converts it into a generic event and publishes it to the `homeassistant` channel.
3. The HA websocket client receives that event and triggers the appropriate local service or automation.

If HA also wants to publish local state changes or events into the proxy, it can send JSON messages that include `source`, `channel`, and `payload`.

This keeps HA unexposed to the internet while still participating fully in the proxy event bus.

## Example payloads

Generic event:
```json
{
  "source": "custom",
  "channel": "homeassistant",
  "payload": {
    "text": "Hello from a local integration"
  }
}
```

Home Assistant-style event:
```json
{
  "source": "homeassistant",
  "channel": "homeassistant",
  "payload": {
    "event_type": "state_changed",
    "entity_id": "light.kitchen",
    "state": "on"
  }
}
```

## Example usage
```bash
curl -X POST http://127.0.0.1:1558/api/v1/event \
  -H "Authorization: Basic <base64-credentials>" \
  -H "Content-Type: application/json" \
  -d '{"source":"homeassistant","channel":"homeassistant","payload":{"event_type":"state_changed","entity_id":"light.kitchen","state":"on"}}'
```
