import logging
from collections.abc import Iterator
from contextlib import contextmanager

from src.shopping_reminder.logger import get_logger


@contextmanager
def _root_handlers(*handlers: logging.Handler) -> Iterator[list[logging.Handler]]:
    """ルートロガーのハンドラーを handlers だけにし、抜けるときに元に戻す

    pytest はテストの実行中にルートロガーにハンドラーを付けるので、テストの中で置き換える
    """
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers[:] = list(handlers)
    try:
        yield root.handlers
    finally:
        root.handlers[:] = saved


class TestGetLogger:
    def test_propagates_to_root_logger(self) -> None:
        # OTel の計装（opentelemetry-instrumentation-logging）はルートロガーにハンドラーを付けるので、
        # アプリのログはルートまで届かないといけない
        logger = get_logger("test_logger.propagate")

        assert logger.propagate is True
        assert logger.handlers == []
        assert logger.level == logging.INFO

    def test_adds_stream_handler_to_root_without_handlers(self) -> None:
        with _root_handlers() as handlers:
            get_logger("test_logger.no_root_handlers")
            added = handlers[:]

        assert len(added) == 1
        assert isinstance(added[0], logging.StreamHandler)

    def test_keeps_existing_root_handlers(self) -> None:
        # Lambda では、ランタイムと OTel の計装がルートロガーにハンドラーを付けている
        existing = logging.NullHandler()
        with _root_handlers(existing) as handlers:
            get_logger("test_logger.with_root_handlers")
            after = handlers[:]

        assert after == [existing]
