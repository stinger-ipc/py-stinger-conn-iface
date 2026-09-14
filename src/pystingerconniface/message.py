from __future__ import annotations

from dataclasses import dataclass, field

from .contenttype import ContentType


@dataclass
class Message:
    topic: str
    payload: bytes
    qos: int
    retain: bool = False
    content_type: str | ContentType | None = None
    correlation_data: bytes | None = None
    response_topic: str | None = None
    subscription_ids: list[int] = field(default_factory=list)  # Ignored on publish
    message_expiry_interval: int | None = None
    user_properties: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.user_properties is None:
            self.user_properties = dict()

    def set_user_property(self, key: str, value: str) -> None:
        if self.user_properties is None:
            self.user_properties = dict()
        self.user_properties[key] = value
