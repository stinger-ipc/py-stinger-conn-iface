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
