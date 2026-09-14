from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Callable

from .message import Message

MessageCallback = Callable[[Message], None]


class IBrokerConnection(ABC):

    @abstractmethod
    def publish(self, message: Message) -> Future[None]:
        """
        Publishes a message to the provided topic with the provided parameters.  If the
        connection to the broker is not established, the message may be queued until the
        connection is established.
        """
        pass

    @abstractmethod
    def subscribe(self, topic: str, callback: MessageCallback | None = None, qos: int = 1) -> int:
        """
        Subscribes to the provided topic.  May queue the subscription until the connection to
        the broker is established.  When a message is received on the topic, the provided
        callback will be executed if provided.
        Returns a subscription identifier for the subscription.
        """
        pass

    @abstractmethod
    def add_message_callback(self, callback: MessageCallback) -> None:
        """
        The provided callback is called for all received messages that do not have a specific
        callback registered via the subscribe method.
        """
        pass

    @abstractmethod
    def is_topic_sub(self, topic: str, sub: str) -> bool:
        """Returns True if the provided topic matches the provided subscription filter."""
        pass

    @property
    @abstractmethod
    def online_topic(self) -> str | None:
        pass

    @property
    @abstractmethod
    def client_id(self) -> str:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if the connection to the broker is established."""
        pass

    def unpublish_retained(self, topic: str) -> None:
        msg = Message(topic=topic, payload=b"", qos=1, retain=True)
        self.publish(msg)
