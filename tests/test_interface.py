from __future__ import annotations

from concurrent.futures import Future

import pytest

from pystingerconniface.interface import IBrokerConnection, MessageCallback
from pystingerconniface.message import Message


class FakeBrokerConnection(IBrokerConnection):
    def __init__(self) -> None:
        self.published: list[Message] = []

    def publish(self, message: Message) -> Future[None]:
        self.published.append(message)
        future: Future[None] = Future()
        future.set_result(None)
        return future

    def subscribe(self, topic: str, callback: MessageCallback | None = None, qos: int = 1) -> int:
        return 1

    def add_message_callback(self, callback: MessageCallback) -> None:
        pass

    def is_topic_sub(self, topic: str, sub: str) -> bool:
        return topic == sub

    @property
    def online_topic(self) -> str | None:
        return None

    @property
    def client_id(self) -> str:
        return "fake-client"

    def is_connected(self) -> bool:
        return True


def test_cannot_instantiate_abstract_class() -> None:
    with pytest.raises(TypeError):
        IBrokerConnection()  # type: ignore[abstract]


def test_unpublish_retained_publishes_empty_retained_message() -> None:
    conn = FakeBrokerConnection()

    conn.unpublish_retained("some/topic")

    assert len(conn.published) == 1
    published = conn.published[0]
    assert published.topic == "some/topic"
    assert published.payload == b""
    assert published.qos == 1
    assert published.retain is True
