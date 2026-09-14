# py-stinger-conn-iface

The interface for Python stinger connections.

This package defines the abstract, broker-agnostic interface that
[stinger-ipc](https://github.com/stinger-ipc) broker connection implementations (e.g. MQTT)
implement, along with the small set of value types (`Message`, `ContentType`) used to describe
messages passing through that interface. It contains no broker-specific logic itself.

Supports Python 3.7+.

## Installation

```bash
pip install py-stinger-conn-iface
```

Or, with `uv`:

```bash
uv add py-stinger-conn-iface
```

## Contents

### `Message`

A dataclass describing a single message to publish or that has been received.

```python
from pystingerconniface import Message

msg = Message(topic="devices/123/status", payload=b'{"online": true}', qos=1, retain=True)
msg.set_user_property("trace-id", "abc123")
```

| Field | Type | Description |
| --- | --- | --- |
| `topic` | `str` | The topic the message is published to or received on. |
| `payload` | `bytes` | The raw message payload. |
| `qos` | `int` | The quality-of-service level for the message. |
| `retain` | `bool` | Whether the broker should retain the message on the topic. |
| `content_type` | `str \| ContentType \| None` | The content type of the payload, if any. |
| `correlation_data` | `bytes \| None` | Correlation data for request/response patterns. |
| `response_topic` | `str \| None` | Topic the receiver should reply to, if any. |
| `subscription_ids` | `list[int]` | Subscription identifiers a received message matched. Ignored on publish. |
| `message_expiry_interval` | `int \| None` | Seconds after which the broker may discard the message. |
| `user_properties` | `dict[str, str]` | Arbitrary user-defined key/value metadata. |

`Message` also converts to and from the shapes MQTT client libraries use.  No client library
is a dependency of this package: the inbound conversions are duck-typed, and `paho_kwargs()`
imports paho-mqtt only when it is called.

```python
# Publishing with paho-mqtt (requires paho-mqtt to be installed by the caller).
client.publish(**msg.paho_kwargs())

# Receiving, in a paho-mqtt on_message callback.
msg = Message.from_paho_message(paho_msg)
```

| Method | Description |
| --- | --- |
| `mqtt_properties()` | The message's MQTT v5 PUBLISH properties as a dict keyed by their spec names (`ContentType`, `UserProperty`, ...).  Unset properties are omitted. |
| `set_mqtt_properties(properties)` | Applies such a dict onto the message.  Unknown keys are ignored, so a client library's property object can be passed through as-is. |
| `Message.from_mqtt_message(msg)` | Builds a `Message` from any received-message object with `topic`, `payload`, `qos` and `retain` attributes, plus an optional `properties` mapping or attribute carrier. |
| `paho_kwargs()` | The keyword arguments for a paho-mqtt `Client.publish()` call, including a populated `Properties` object. |
| `Message.from_paho_message(paho_msg)` | `from_mqtt_message()` under the name paho callers expect. |

### `ContentType`

A `str` subclass for parsing and constructing HTTP-style `Content-Type` header values,
including their parameters (e.g. `charset`).

```python
from pystingerconniface import ContentType

ct = ContentType("application/json; charset=utf-8")
ct == "application/json"          # True, ContentType is a str subclass
ct.parameters                     # {"charset": "utf-8"}
ct.charset                        # "utf-8" (also available as an attribute)
ct.to_header()                    # "application/json; charset=utf-8"
```

### `IBrokerConnection`

An abstract base class describing the operations a broker connection implementation must
provide: publishing messages, subscribing to topics, registering message callbacks, and
reporting connection state.

```python
from pystingerconniface import IBrokerConnection, Message

class MyBrokerConnection(IBrokerConnection):
    def publish(self, message: Message):
        ...

    def subscribe(self, topic, callback=None, qos=1):
        ...

    def add_message_callback(self, callback):
        ...

    def is_topic_sub(self, topic, sub):
        ...

    @property
    def online_topic(self):
        ...

    @property
    def client_id(self):
        ...

    def is_connected(self):
        ...
```

`IBrokerConnection` also provides a concrete `unpublish_retained(topic)` helper that publishes
an empty, retained message to clear a previously retained message from a topic.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync              # install runtime and dev dependencies
uv run pytest         # run the test suite
uv run ruff check .   # lint
uv run black .        # format
uv run mypy src tests # type check
```

## License

MIT — see [LICENSE](LICENSE).
