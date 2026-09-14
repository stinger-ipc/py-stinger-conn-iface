import sys
import types

import pytest

from pystingerconniface.contenttype import ContentType
from pystingerconniface.message import Message


def test_defaults() -> None:
    msg = Message(topic="a/b", payload=b"payload", qos=1)

    assert msg.topic == "a/b"
    assert msg.payload == b"payload"
    assert msg.qos == 1
    assert msg.retain is False
    assert msg.content_type is None
    assert msg.correlation_data is None
    assert msg.response_topic is None
    assert msg.subscription_ids == []
    assert msg.message_expiry_interval is None
    assert msg.user_properties == {}


def test_user_properties_default_is_not_shared_between_instances() -> None:
    msg1 = Message(topic="a", payload=b"", qos=0)
    msg2 = Message(topic="b", payload=b"", qos=0)

    msg1.set_user_property("key", "value")

    assert msg1.user_properties == {"key": "value"}
    assert msg2.user_properties == {}


def test_user_properties_none_is_normalized_to_empty_dict() -> None:
    msg = Message(topic="a", payload=b"", qos=0, user_properties=None)  # type: ignore[arg-type]

    assert msg.user_properties == {}


def test_set_user_property_adds_and_overwrites() -> None:
    msg = Message(topic="a", payload=b"", qos=0)

    msg.set_user_property("key", "value")
    msg.set_user_property("key", "new-value")
    msg.set_user_property("other", "1")

    assert msg.user_properties == {"key": "new-value", "other": "1"}


def test_set_user_property_when_dict_was_reset_to_none() -> None:
    msg = Message(topic="a", payload=b"", qos=0)
    msg.user_properties = None  # type: ignore[assignment]

    msg.set_user_property("key", "value")

    assert msg.user_properties == {"key": "value"}


class FakeReceivedMessage:
    """Stands in for a client library's received-message object (e.g. paho's MQTTMessage)."""

    def __init__(
        self,
        topic: object,
        payload: bytes,
        qos: int = 1,
        retain: bool = False,
        properties: object = None,
    ) -> None:
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain
        if properties is not None:
            self.properties = properties


class FakeProperties:
    """Stands in for a property object that carries properties as attributes."""

    def __init__(self, **properties: object) -> None:
        self.packetType = 3  # paho's Properties carries bookkeeping attributes too.
        for name, value in properties.items():
            setattr(self, name, value)


def test_mqtt_properties_omits_unset_properties() -> None:
    msg = Message(topic="a", payload=b"", qos=0)

    assert msg.mqtt_properties() == {}


def test_mqtt_properties_includes_every_set_property() -> None:
    msg = Message(
        topic="a",
        payload=b"",
        qos=0,
        content_type=ContentType("application/json; charset=utf-8"),
        correlation_data=b"corr",
        response_topic="a/response",
        message_expiry_interval=60,
        user_properties={"key": "value"},
    )

    assert msg.mqtt_properties() == {
        "ContentType": "application/json; charset=utf-8",
        "CorrelationData": b"corr",
        "ResponseTopic": "a/response",
        "MessageExpiryInterval": 60,
        "UserProperty": [("key", "value")],
    }


def test_mqtt_properties_passes_a_plain_string_content_type_through() -> None:
    msg = Message(topic="a", payload=b"", qos=0, content_type="application/json")

    assert msg.mqtt_properties()["ContentType"] == "application/json"


def test_set_mqtt_properties_ignores_unknown_keys() -> None:
    msg = Message(topic="a", payload=b"", qos=0)

    msg.set_mqtt_properties({"PayloadFormatIndicator": 1, "packetType": 3})

    assert msg.content_type is None
    assert msg.user_properties == {}


def test_set_mqtt_properties_accepts_a_single_user_property_pair() -> None:
    msg = Message(topic="a", payload=b"", qos=0)

    msg.set_mqtt_properties({"UserProperty": ("key", "value")})

    assert msg.user_properties == {"key": "value"}


def test_from_mqtt_message_without_properties() -> None:
    msg = Message.from_mqtt_message(FakeReceivedMessage("a/b", b"payload", qos=2, retain=True))

    assert (msg.topic, msg.payload, msg.qos, msg.retain) == ("a/b", b"payload", 2, True)
    assert msg.mqtt_properties() == {}


def test_from_mqtt_message_decodes_a_bytes_topic() -> None:
    msg = Message.from_mqtt_message(FakeReceivedMessage(b"a/b", b""))

    assert msg.topic == "a/b"


def test_from_mqtt_message_reads_properties_from_an_attribute_carrier() -> None:
    properties = FakeProperties(
        ContentType="application/json; charset=utf-8",
        CorrelationData=b"corr",
        ResponseTopic="a/response",
        MessageExpiryInterval=60,
        UserProperty=[("key", "value")],
        SubscriptionIdentifier=[1, 2],
    )

    msg = Message.from_mqtt_message(FakeReceivedMessage("a/b", b"", properties=properties))

    assert isinstance(msg.content_type, ContentType)
    assert msg.content_type == "application/json"
    assert msg.content_type.charset == "utf-8"
    assert msg.correlation_data == b"corr"
    assert msg.response_topic == "a/response"
    assert msg.message_expiry_interval == 60
    assert msg.user_properties == {"key": "value"}
    assert msg.subscription_ids == [1, 2]


def test_from_mqtt_message_reads_properties_from_a_mapping() -> None:
    msg = Message.from_mqtt_message(
        FakeReceivedMessage("a/b", b"", properties={"ResponseTopic": "a/response"})
    )

    assert msg.response_topic == "a/response"


def test_from_mqtt_message_wraps_a_scalar_subscription_identifier() -> None:
    msg = Message.from_mqtt_message(
        FakeReceivedMessage("a/b", b"", properties=FakeProperties(SubscriptionIdentifier=7))
    )

    assert msg.subscription_ids == [7]


def test_round_trip_through_mqtt_properties() -> None:
    original = Message(
        topic="a/b",
        payload=b"payload",
        qos=1,
        retain=True,
        content_type=ContentType("application/json"),
        correlation_data=b"corr",
        response_topic="a/response",
        message_expiry_interval=60,
        user_properties={"key": "value"},
    )

    received = Message.from_mqtt_message(
        FakeReceivedMessage(
            original.topic,
            original.payload,
            qos=original.qos,
            retain=original.retain,
            properties=original.mqtt_properties(),
        )
    )

    assert received == original


class FakePahoProperties:
    """Stands in for paho's `Properties`, which takes a packet type and holds attributes."""

    def __init__(self, packet_type: int) -> None:
        self.packetType = packet_type


def _install_fake_paho(monkeypatch: pytest.MonkeyPatch) -> None:
    properties_module = types.ModuleType("paho.mqtt.properties")
    properties_module.Properties = FakePahoProperties  # type: ignore[attr-defined]
    for name in ("paho", "paho.mqtt"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, "paho.mqtt.properties", properties_module)


def test_paho_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_paho(monkeypatch)
    msg = Message(
        topic="a/b",
        payload=b"payload",
        qos=2,
        retain=True,
        content_type=ContentType("application/json; charset=utf-8"),
        correlation_data=b"corr",
        response_topic="a/response",
        message_expiry_interval=60,
        user_properties={"key": "value"},
    )

    kwargs = msg.paho_kwargs()

    properties = kwargs.pop("properties")
    assert kwargs == {"topic": "a/b", "payload": b"payload", "qos": 2, "retain": True}
    assert properties.packetType == 3  # PacketTypes.PUBLISH
    assert properties.ContentType == "application/json; charset=utf-8"
    assert properties.CorrelationData == b"corr"
    assert properties.ResponseTopic == "a/response"
    assert properties.MessageExpiryInterval == 60
    assert properties.UserProperty == [("key", "value")]


def test_paho_kwargs_sets_no_properties_for_a_bare_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_paho(monkeypatch)
    msg = Message(topic="a", payload=b"", qos=0)

    properties = msg.paho_kwargs()["properties"]

    assert vars(properties) == {"packetType": 3}


def test_from_paho_message() -> None:
    paho_msg = FakeReceivedMessage(
        b"a/b", b"payload", qos=1, properties=FakeProperties(ResponseTopic="a/response")
    )

    msg = Message.from_paho_message(paho_msg)

    assert msg.topic == "a/b"
    assert msg.response_topic == "a/response"
