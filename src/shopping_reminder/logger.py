import logging

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    """
    アプリケーション用のロガーを取得する共通関数

    ログはルートロガーのハンドラーが出力する。Lambda では、ランタイムのハンドラーが CloudWatch Logs に出し、
    opentelemetry-instrumentation-logging のハンドラーが OTel のログとして Grafana Cloud に送る。
    ルートロガーにハンドラーが無いとき（ローカルで python から直接動かすときなど）だけ、標準エラーに出す。

    Args:
        name: ロガー名（通常は__name__を指定）

    Returns:
        設定されたロガーインスタンス
    """
    # ルートロガーにハンドラーがあるときは何もしない
    logging.basicConfig(format=LOG_FORMAT)

    logger = logging.getLogger(name or __name__)
    # ルートロガーのレベルに関わらず、INFO 以上を出す
    logger.setLevel(logging.INFO)
    return logger
