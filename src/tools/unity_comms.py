from __future__ import annotations

from collections import deque
from typing import Deque, Optional


class UnityBridge:
    def __init__(self) -> None:
        self._queue: Deque[str] = deque()

    def queue_message(self, message: str) -> None:
        self._queue.append(message)

    def dequeue_message(self) -> Optional[str]:
        if self._queue:
            return self._queue.popleft()
        return None

    def pending(self) -> int:
        return len(self._queue)
