"""アプリが作る OTel の span とメトリクスのテスト"""

import json
from typing import Any
from unittest.mock import Mock, patch

from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from src.shopping_reminder.config import Config
from src.shopping_reminder.lambda_handler import ShoppingReminderProcessor
from src.shopping_reminder.models import ShoppingItem
from src.shopping_reminder.notify_client import NotifyClient
from src.shopping_reminder.notion_client import NotionClient

CONFIG = Config.from_dict(
    {
        "NOTION_API_KEY": "secret_test_key",
        "NOTION_DATABASE_ID": "test_database_id",
        "NOTIFY_API_KEY": "test_notify_key",
        "NOTIFY_API_URL": "https://example.com/prod",
    }
)


def _span(exporter: InMemorySpanExporter, name: str) -> ReadableSpan:
    spans = [s for s in exporter.get_finished_spans() if s.name == name]
    assert len(spans) == 1, f"span {name!r} が1つではない: {spans}"
    return spans[0]


def _metric_points(reader: InMemoryMetricReader, name: str) -> list[Any]:
    data = reader.get_metrics_data()
    if data is None:
        return []
    return [
        point
        for resource_metrics in data.resource_metrics
        for scope_metrics in resource_metrics.scope_metrics
        for metric in scope_metrics.metrics
        if metric.name == name
        for point in metric.data.data_points
    ]


def _notion_page(names: list[str], has_more: bool, next_cursor: str | None = None) -> Mock:
    response = Mock()
    response.read.return_value = json.dumps(
        {
            "results": [
                {
                    "id": f"id-{name}",
                    "properties": {
                        "名前": {"title": [{"text": {"content": name}}]},
                        "完了": {"checkbox": False},
                    },
                }
                for name in names
            ],
            "has_more": has_more,
            "next_cursor": next_cursor,
        }
    ).encode("utf-8")
    response.getcode.return_value = 200
    return response


class TestNotionClientTelemetry:
    @patch("urllib.request.urlopen")
    def test_query_unchecked_items_span(
        self, mock_urlopen: Mock, span_exporter: InMemorySpanExporter
    ) -> None:
        mock_urlopen.return_value.__enter__.side_effect = [
            _notion_page(["牛乳", "パン"], has_more=True, next_cursor="cursor-1"),
            _notion_page(["卵"], has_more=False),
        ]

        NotionClient(CONFIG).query_unchecked_items()

        span = _span(span_exporter, "query_unchecked_items")
        assert span.attributes is not None
        assert span.attributes["notion.page_count"] == 2
        assert span.attributes["notion.unchecked_items_count"] == 3


class TestNotifyClientTelemetry:
    @patch("urllib.request.urlopen")
    def test_send_notification_span_and_counter(
        self,
        mock_urlopen: Mock,
        span_exporter: InMemorySpanExporter,
        metric_reader: InMemoryMetricReader,
    ) -> None:
        response = Mock()
        response.read.return_value = b'{"message": "ok"}'
        response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = response

        NotifyClient(CONFIG).send_notification([ShoppingItem("1", "牛乳", False)])

        span = _span(span_exporter, "send_notification")
        assert span.attributes is not None
        assert span.attributes["notify.item_count"] == 1
        assert span.status.status_code is not StatusCode.ERROR

        points = _metric_points(metric_reader, "shopping_reminder.notifications.sent")
        assert [p.value for p in points] == [1]

    @patch("urllib.request.urlopen")
    def test_send_notification_without_items_does_not_count(
        self,
        mock_urlopen: Mock,
        span_exporter: InMemorySpanExporter,
        metric_reader: InMemoryMetricReader,
    ) -> None:
        NotifyClient(CONFIG).send_notification([])

        span = _span(span_exporter, "send_notification")
        assert span.attributes is not None
        assert span.attributes["notify.item_count"] == 0
        assert _metric_points(metric_reader, "shopping_reminder.notifications.sent") == []
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_send_notification_failure_marks_span_as_error(
        self,
        mock_urlopen: Mock,
        span_exporter: InMemorySpanExporter,
        metric_reader: InMemoryMetricReader,
    ) -> None:
        response = Mock()
        response.read.return_value = b'{"message": "bad request"}'
        response.getcode.return_value = 400
        mock_urlopen.return_value.__enter__.return_value = response

        result = NotifyClient(CONFIG).send_notification([ShoppingItem("1", "牛乳", False)])

        assert result.success is False
        span = _span(span_exporter, "send_notification")
        assert span.status.status_code is StatusCode.ERROR
        assert any(event.name == "exception" for event in span.events)
        assert _metric_points(metric_reader, "shopping_reminder.notifications.sent") == []


class TestProcessorTelemetry:
    def _processor(self, items: list[ShoppingItem] | Exception) -> ShoppingReminderProcessor:
        processor = ShoppingReminderProcessor(CONFIG)
        notion = Mock()
        if isinstance(items, Exception):
            notion.query_unchecked_items.side_effect = items
        else:
            notion.query_unchecked_items.return_value = items
        processor.notion_client = notion
        processor.notify_client = Mock()
        return processor

    def test_process_span_and_histogram(
        self, span_exporter: InMemorySpanExporter, metric_reader: InMemoryMetricReader
    ) -> None:
        items = [ShoppingItem("1", "牛乳", False), ShoppingItem("2", "パン", False)]

        self._processor(items).process(dry_run=True)

        span = _span(span_exporter, "process")
        assert span.attributes is not None
        assert span.attributes["shopping_reminder.dry_run"] is True

        points = _metric_points(metric_reader, "shopping_reminder.items.unchecked")
        assert len(points) == 1
        assert points[0].sum == 2
        assert points[0].count == 1
        assert dict(points[0].attributes) == {"dry_run": True}

    def test_process_error_marks_span_as_error(
        self, span_exporter: InMemorySpanExporter, metric_reader: InMemoryMetricReader
    ) -> None:
        result = self._processor(RuntimeError("boom")).process()

        assert result.success is False
        span = _span(span_exporter, "process")
        assert span.attributes is not None
        assert span.attributes["shopping_reminder.dry_run"] is False
        assert span.status.status_code is StatusCode.ERROR
        assert any(event.name == "exception" for event in span.events)
        assert _metric_points(metric_reader, "shopping_reminder.items.unchecked") == []
