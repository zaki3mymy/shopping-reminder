import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    アプリケーション用のロガーを取得する共通関数

    Args:
        name: ロガー名（通常は__name__を指定）

    Returns:
        設定されたロガーインスタンス
    """
    logger = logging.getLogger(name or __name__)

    # ロガーが既に設定されている場合は再設定をスキップ
    if logger.handlers:
        return logger

    # CloudWatchでの可視性を高めるためのログ設定
    logger.setLevel(logging.INFO)

    # コンソールハンドラーの作成
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # フォーマッターの設定
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # 重複ログを防ぐ
    logger.propagate = False

    return logger
