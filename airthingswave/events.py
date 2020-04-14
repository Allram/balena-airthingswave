import _thread
import contextlib
import threading
from types import TracebackType
from typing import ContextManager, Optional, Type

DUMMY: ContextManager[None] = contextlib.nullcontext()


def in_main_thread() -> bool:
    return threading.current_thread() is threading.main_thread()


class TimeoutInterruptContextManager:
    def __init__(self, timeout: float) -> None:
        self._timeout = timeout
        self._entered = False
        self._interrupted = False
        self._finished = threading.Event()

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        if self._entered:
            raise RuntimeError("can't set timeout while entered")

        self._timeout = value

    @property
    def entered(self) -> bool:
        return self._entered

    def __interrupter(self) -> None:
        if self._finished.wait(self._timeout):
            return

        self._interrupted = True
        _thread.interrupt_main()

    def __enter__(self) -> None:
        assert in_main_thread(), "can only be used in main thread"
        assert not self._entered, "cannot use recursively"

        self._entered = True
        self._interrupted = False
        self._finished.clear()

        threading.Thread(target=self.__interrupter).start()

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self._finished.set()
        self._entered = False

        if self._interrupted and isinstance(exc_val, KeyboardInterrupt):
            raise TimeoutError from None


def timeout_interrupt(timeout: Optional[float], ignore_wrong_thread: bool = True) -> ContextManager[None]:
    if timeout is None or (not in_main_thread() and ignore_wrong_thread):
        return DUMMY

    return TimeoutInterruptContextManager(timeout)
