"""OTel のテレメトリをテストで確かめるための設定

本番では Lambda の Python 計装レイヤーが TracerProvider・MeterProvider を設定する。
テストでは SDK のプロバイダーをメモリに書き出すように設定し、アプリが作った span とメトリクスを読む。
グローバルなプロバイダーは一度しか設定できないため、テストのセッションの最初に一度だけ設定する。
"""

from collections.abc import Iterator

import pytest
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import Counter, Histogram, MeterProvider
from opentelemetry.sdk.metrics.export import AggregationTemporality, InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_span_exporter = InMemorySpanExporter()
_tracer_provider = TracerProvider()
_tracer_provider.add_span_processor(SimpleSpanProcessor(_span_exporter))
trace.set_tracer_provider(_tracer_provider)

# テストごとの値を読めるよう、前回読んでからの差分（DELTA）で読む
_metric_reader = InMemoryMetricReader(
    preferred_temporality={
        Counter: AggregationTemporality.DELTA,
        Histogram: AggregationTemporality.DELTA,
    }
)
metrics.set_meter_provider(MeterProvider(metric_readers=[_metric_reader]))


@pytest.fixture
def span_exporter() -> Iterator[InMemorySpanExporter]:
    """テストの中で終わった span を読むための exporter"""
    _span_exporter.clear()
    yield _span_exporter
    _span_exporter.clear()


@pytest.fixture
def metric_reader() -> InMemoryMetricReader:
    """テストの中で記録したメトリクスを読むための reader"""
    # それまでに記録された値を読み捨てる
    _metric_reader.get_metrics_data()
    return _metric_reader
