from __future__ import annotations  # allow forward references in type hints

from threading import Event, Lock
from typing import Any, Callable, Optional, cast
from ska_tango_base.executor.executor_component_manager import (
    TaskExecutorComponentManager,
)

MAX_QUEUED_COMMANDS = 64

__all__ = ["Mac200GbComponentManager"]

class Mac200GbComponentManager(TaskExecutorComponentManager):
    def __init__(
        self: Mac200GbComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, max_queue_size=MAX_QUEUED_COMMANDS, **kwargs)
