from __future__ import annotations

import importlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .contenttype import ContentType

_PAHO_PUBLISH_PACKET_TYPE = 3


@dataclass
class Message:
    topic: str
    payload: bytes
    qos: int
    retain: bool = False
    content_type: Union[str, ContentType, None] = None
    correlation_data: Optional[bytes] = None
    response_topic: Optional[str] = None
    subscription_ids: List[int] = field(default_factory=list)  # Ignored on publish
    message_expiry_interval: Optional[int] = None
    user_properties: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.user_properties is None:
            self.user_properties = dict()

    def set_user_property(self, key: str, value: str) -> None:
        if self.user_properties is None:
            self.user_properties = dict()
        self.user_properties[key] = value

    def mqtt_properties(self) -> Dict[str, Any]:
        """
        The MQTT v5 PUBLISH properties for this message, keyed by their spec names (the same
        names MQTT client libraries use as attributes on their property objects).  Properties
        that are unset on this message are omitted.
        """
        properties: Dict[str, Any] = {}
        if self.content_type is not None:
            properties["ContentType"] = (
                self.content_type.to_header()
                if isinstance(self.content_type, ContentType)
                else self.content_type
            )
        if self.correlation_data is not None:
            properties["CorrelationData"] = self.correlation_data
        if self.response_topic is not None:
            properties["ResponseTopic"] = self.response_topic
        if self.message_expiry_interval is not None:
            properties["MessageExpiryInterval"] = self.message_expiry_interval
        if self.user_properties:
            properties["UserProperty"] = list(self.user_properties.items())
        return properties

    def set_mqtt_properties(self, properties: Mapping[str, Any]) -> None:
        """
        Applies MQTT v5 properties, keyed by their spec names, onto this message.  Unknown and
        absent keys are ignored, so a client library's property object can be passed through
        as-is (see `from_mqtt_message`).
        """
        user_properties = properties.get("UserProperty")
        if user_properties is not None:
            if isinstance(user_properties, tuple):  # A single key/value pair.
                user_properties = [user_properties]
            self.user_properties = dict(user_properties)
        content_type = properties.get("ContentType")
        if isinstance(content_type, str):
            self.content_type = ContentType(content_type)
        if "CorrelationData" in properties:
            self.correlation_data = properties["CorrelationData"]
        if "ResponseTopic" in properties:
            self.response_topic = properties["ResponseTopic"]
        if "MessageExpiryInterval" in properties:
            self.message_expiry_interval = properties["MessageExpiryInterval"]
        subscription_ids = properties.get("SubscriptionIdentifier")
        if subscription_ids is not None:
            self.subscription_ids = (
                list(subscription_ids) if isinstance(subscription_ids, list) else [subscription_ids]
            )

    @classmethod
    def from_mqtt_message(cls, msg: Any) -> Message:
        """
        Builds a Message from a received message object from an MQTT client library.  The
        object is only duck-typed: it needs `topic`, `payload`, `qos` and `retain` attributes,
        and optionally a `properties` attribute that is either a mapping of MQTT v5 property
        names to values or an object carrying them as attributes.
        """
        topic = msg.topic
        if isinstance(topic, bytes):
            topic = topic.decode("utf-8")
        msg_obj = cls(
            topic=topic,
            payload=msg.payload,
            qos=msg.qos,
            retain=msg.retain,
        )
        properties = getattr(msg, "properties", None)
        if properties is not None:
            msg_obj.set_mqtt_properties(
                properties if isinstance(properties, Mapping) else vars(properties)
            )
        return msg_obj

    def paho_kwargs(self) -> Dict[str, Any]:
        """
        The keyword arguments for a paho-mqtt `Client.publish()` call for this message.

        paho-mqtt is not a dependency of this package; it is imported here, at call time, so
        that only callers who want paho-shaped output need it installed.
        """
        try:
            properties_module = importlib.import_module("paho.mqtt.properties")
        except ImportError as exc:  # pragma: no cover - depends on the caller's environment
            raise ImportError("Message.paho_kwargs() requires paho-mqtt to be installed.") from exc
        props = properties_module.Properties(_PAHO_PUBLISH_PACKET_TYPE)
        for name, value in self.mqtt_properties().items():
            setattr(props, name, value)
        return {
            "topic": self.topic,
            "payload": self.payload,
            "qos": self.qos,
            "retain": self.retain,
            "properties": props,
        }

    @classmethod
    def from_paho_message(cls, paho_msg: Any) -> Message:
        """Builds a Message from a paho-mqtt `MQTTMessage`.  See `from_mqtt_message`."""
        return cls.from_mqtt_message(paho_msg)
