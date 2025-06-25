from __future__ import annotations
from threading import Thread
from typing import Any, Callable, Generic, ParamSpec, TypeVar
from functools import wraps


P = ParamSpec('P')
R = TypeVar('R')


class NonBlockingFunction(Generic[P, R]):
    """Class that wraps a given function to run it in a thread and return a result."""

    def __init__(self, fn: Callable[P, R], *args, **kwargs):
        self._result_storage = [None]
        self._thread = Thread(target=self._wrap_fn(fn), args=(self._result_storage, *args,), kwargs=kwargs)

    def _wrap_fn(self, fn: Callable[P, R]) -> Callable[[list[R], Any], None]:
        def wrapped_fn(result_storage: list[R], *args, **kwargs):
            result_storage[0] = fn(*args, **kwargs)
        return wrapped_fn
    
    def start(self) -> None:
        """Start the function thread."""
        self._thread.start()

    def join(self) -> None:
        """Join the function thread."""
        self._thread.join()

    def get_result(self) -> R:
        """Get the stored result from the function execution. Will return None if the function has not completed yet."""
        return self._result_storage[0]

    def await_result(self) -> R:
        """Wait for the function to complete and return the stored result."""
        self.join()
        return self.get_result()
    
    @staticmethod
    def await_all(*fns: NonBlockingFunction) -> list[Any]:
        """Wait for all of the specified non-blocking functions to complete and return a list of all of their results."""
        for fn in fns:
            fn.join()
        return [fn.get_result() for fn in fns]


def non_blocking(fn: Callable[P, R]):
    """Decorator which turns a function into a non-blocking function."""
    @wraps(fn)
    def inner(*args, **kwargs) -> NonBlockingFunction[P, R]:
        nb_fn = NonBlockingFunction[P, R](fn, *args, **kwargs)
        nb_fn.start()
        return nb_fn
    return inner
